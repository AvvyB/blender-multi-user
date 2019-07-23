import threading
import logging
import zmq
import time
from replication import ReplicatedDatablock, RepCommand,RepDeleteCommand
from replication_graph import ReplicationGraph

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

STATE_INITIAL = 0
STATE_SYNCING = 1
STATE_ACTIVE = 2


class Client(object):
    def __init__(self,factory=None, id='default'):
        assert(factory)

        self._rep_store = ReplicationGraph()
        self._net_client = ClientNetService(
            store_reference=self._rep_store,
            factory=factory,
            id=id)
        self._factory = factory

    def connect(self,address="127.0.0.1",port=5560):
        """
        Connect to the server
        """
        self._net_client.connect(address=address,port=port)

    def disconnect(self):
        """
        Disconnect from server, reset the client
        """
        self._net_client.stop()

    @property
    def state(self):
        """
        Return the client state
        0: STATE_INITIAL
        1: STATE_SYNCING
        2: STATE_ACTIVE
        """
        return self._net_client.state

    def register(self, object):
        """
        Register a new item for replication
        TODO: Dig in the replication comportement,
        find a better way to handle replication behavior
        """
        assert(object)
        
        # Construct the coresponding replication type
        new_item = self._factory.construct_from_dcc(object)(owner="client", pointer=object)

        if new_item:
            logger.info("Registering {} on {}".format(object,new_item.uuid))
            new_item.store(self._rep_store)
            
            logger.info("Pushing new registered value")
            new_item.push(self._net_client.publish)
            return new_item.uuid
            
        else:
            raise TypeError("Type not supported")

    def pull(self,object=None):
        """
        Asynchonous pull
        Here we want to pull all waiting changes and apply them
        """
        pass
    
    def unregister(self,object_uuid,clean=False):
        """
        Unregister for replication the given
        object.
        The clean option purpose is to remove
        the pointer data's
        """

        if object_uuid in self._rep_store.keys():
            delete_command = RepDeleteCommand(owner='client', buffer=object_uuid)
            delete_command.store(self._rep_store)
            delete_command.push(self._net_client.publish)
        else:
            raise KeyError("Cannot unregister key")
            

class ClientNetService(threading.Thread):
    def __init__(self,store_reference=None, factory=None,id="default"):

        # Threading
        threading.Thread.__init__(self)
        self.name = "ClientNetLink"
        self.daemon = True
        
        self._exit_event = threading.Event()
        self._factory = factory
        self._store_reference = store_reference
        self._id = id

        assert(self._factory)

        # Networking
        self.context = zmq.Context.instance()
        self.state = STATE_INITIAL

    def connect(self,address='127.0.0.1', port=5560):
        """
        Network socket setup
        """
        if self.state == STATE_INITIAL:
            logger.debug("connecting on {}:{}".format(address,port))
            self.snapshot = self.context.socket(zmq.DEALER)
            self.snapshot.setsockopt(zmq.IDENTITY, self._id.encode())
            self.snapshot.connect("tcp://{}:{}".format(address, port))
            
            self.subscriber = self.context.socket(zmq.SUB)
            self.subscriber.setsockopt_string(zmq.SUBSCRIBE, '')
            # self.subscriber.setsockopt(zmq.IDENTITY, self._id.encode())
            self.subscriber.connect("tcp://{}:{}".format(address, port+1))
            self.subscriber.linger = 0
            time.sleep(.5)

            self.publish = self.context.socket(zmq.PUSH)
            self.publish.connect("tcp://{}:{}".format(address, port+2))

            self.start()

    def run(self):
        logger.info("{} online".format(self._id))
        poller = zmq.Poller()
        poller.register(self.snapshot, zmq.POLLIN)
        poller.register(self.subscriber, zmq.POLLIN)
        poller.register(self.publish, zmq.POLLOUT)

        while not self._exit_event.is_set():
            """NET OUT 
                Given the net state we do something:
                INITIAL : Ask for snapshots 
            """
            if self.state == STATE_INITIAL:
                logger.debug('{} : request snapshot'.format(self._id))
                self.snapshot.send(b"SNAPSHOT_REQUEST")
                self.state = STATE_SYNCING
            

            """NET IN 
                Given the net state we do something:
                SYNCING : load snapshots
                ACTIVE : listen for updates 
            """
            items = dict(poller.poll(1))

            if self.snapshot in items:
                if self.state == STATE_SYNCING:
                    datablock = ReplicatedDatablock.pull(self.snapshot, self._factory)

                    if 'SNAPSHOT_END' in datablock.buffer:
                        self.state = STATE_ACTIVE
                        logger.debug('{} : snapshot done'.format(self._id))

                    datablock.store(self._store_reference)

            # We receive updates from the server !
            if self.subscriber in items:
                if self.state == STATE_ACTIVE:
                    logger.debug("{} : Receiving changes from server".format(self._id))
                    datablock = ReplicatedDatablock.pull(self.subscriber, self._factory)
                    datablock.store(self._store_reference)

            if not items:
                logger.error("No request ")
                

        self.snapshot.close()
        self.subscriber.close()
        self.publish.close()

        self._exit_event.clear()
    
    def stop(self):
        self._exit_event.set()

        #Wait the end of the run
        while self._exit_event.is_set():
            time.sleep(.1)

        self.state = 0



class Server():
    def __init__(self,config=None, factory=None):
        self._rep_store = {}
        self._net = ServerNetService(store_reference=self._rep_store, factory=factory)

    def serve(self,port=5560):
        self._net.listen(port=port)

    def state(self):
        return self._net.state

    def stop(self):
        self._net.stop()


class ServerNetService(threading.Thread):
    def __init__(self,store_reference=None, factory=None):
        # Threading
        threading.Thread.__init__(self)
        self.name = "ServerNetLink"
        self.daemon = True
        self._exit_event = threading.Event()

        # Networking
        self._rep_store =  store_reference

        self.context = zmq.Context.instance()
        self.snapshot = None
        self.publisher = None
        self.pull = None
        self.state = 0
        self.factory = factory
        self.clients = {}

    
    def listen(self, port=5560):
        try:
            # Update request
            self.snapshot = self.context.socket(zmq.ROUTER)
            self.snapshot.setsockopt(zmq.IDENTITY, b'SERVER')
            self.snapshot.setsockopt(zmq.RCVHWM, 60)
            self.snapshot.bind("tcp://*:{}".format(port))

            # Update all clients
            self.publisher = self.context.socket(zmq.PUB)
            # self.publisher.setsockopt(zmq.IDENTITY,b'SERVER_DATA')
            self.publisher.setsockopt(zmq.SNDHWM, 60)
            self.publisher.bind("tcp://*:{}".format(port+1))
            self.publisher.setsockopt(zmq.SNDHWM, 60)
            self.publisher.linger = 0

            # Update collector
            self.pull = self.context.socket(zmq.PULL)
            self.pull.setsockopt(zmq.RCVHWM, 60)
            self.pull.bind("tcp://*:{}".format(port+2))

            self.start()    
        except zmq.error.ZMQError:
            logger.error("Address already in use, change net config")

    def add_client(self, identity):
        if identity in self.clients.keys():
            logger.debug("client already added")
        else:
            self.clients[identity.decode()] = identity

    def run(self):
        logger.debug("Server is online")
        poller = zmq.Poller()
        poller.register(self.snapshot, zmq.POLLIN)
        poller.register(self.pull, zmq.POLLIN)

        self.state = STATE_ACTIVE

        while not self._exit_event.is_set():
            # Non blocking poller
            socks = dict(poller.poll(1))

            # Snapshot system for late join (Server - Client)
            if self.snapshot in socks:
                msg = self.snapshot.recv_multipart(zmq.DONTWAIT)

                identity = msg[0]
                request = msg[1]

                self.add_client(identity)

                if request == b"SNAPSHOT_REQUEST":
                    # Sending snapshots
                    for key, item in self._rep_store.items():
                        self.snapshot.send(identity, zmq.SNDMORE)
                        item.push(self.snapshot)
                    
                    # Snapshot end
                    self.snapshot.send(identity, zmq.SNDMORE)
                    RepCommand(owner='server',pointer='SNAPSHOT_END').push(self.snapshot)              
                    

            # Regular update routing (Clients / Server / Clients)
            if self.pull in socks:
                logger.debug("SERVER: Receiving changes from client")
                datablock = ReplicatedDatablock.pull(self.pull, self.factory)
                
                datablock.store(self._rep_store)
                
                # Update all clients
                # for cli_name,cli_id in self.clients.items():
                #     logger.debug("SERVER: Broadcast changes to {}".format(cli_name))
                #     self.publisher.send(cli_id, zmq.SNDMORE)
                #     datablock.push(self.publisher)
                
                datablock.push(self.publisher)
                
        self.snapshot.close()
        self.pull.close()
        self.publisher.close()

        self._exit_event.clear()


    def stop(self):
        self._exit_event.set()

        #Wait the end of the run
        while self._exit_event.is_set():
            time.sleep(.1)

        self.state = 0