import threading
import logging
import zmq
import time
from replication import ReplicatedDatablock, RepCommand

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

STATE_INITIAL = 0
STATE_SYNCING = 1
STATE_ACTIVE = 2


class Client(object):
    def __init__(self,factory=None, id='default'):
        assert(factory)

        self._rep_store = {}
        self._net_client = ClientNetService(
            store_reference=self._rep_store,
            factory=factory,
            id=id)
        self._factory = factory

    def connect(self):
        self._net_client.start()

    def disconnect(self):
        self._net_client.stop()

    def state(self):
        return self._net_client.state

    def register(self, object):
        """
        Register a new item for replication
        """
        assert(object)
        
        new_item = self._factory.construct_from_dcc(object)(owner="client", data=object)

        if new_item:
            logger.info("Registering {} on {}".format(object,new_item.uuid))
            new_item.store(self._rep_store)
            
            logger.info("Pushing changes...")
            new_item.push(self._net_client.publish)
            return new_item.uuid
            
        else:
            raise TypeError("Type not supported")

    def pull(self,object=None):
        pass
    

    def unregister(self,object):
        pass

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

        self.snapshot = self.context.socket(zmq.DEALER)
        self.snapshot.setsockopt(zmq.IDENTITY, self._id.encode())
        self.snapshot.connect("tcp://127.0.0.1:5560")
        
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, '')
        self.subscriber.connect("tcp://127.0.0.1:5561")
        self.subscriber.linger = 0

        self.publish = self.context.socket(zmq.PUSH)
        self.publish.connect("tcp://127.0.0.1:5562")

        self.state = STATE_INITIAL


    def run(self):
        logger.info("{} online".format(self._id))
        poller = zmq.Poller()
        poller.register(self.snapshot, zmq.POLLIN)
        poller.register(self.subscriber, zmq.POLLIN)
        poller.register(self.publish, zmq.POLLOUT)

        while not self._exit_event.is_set():
            """NET OUT 
                Given the net state we do something:
                SYNCING : Ask for snapshots
                ACTIVE : Do nothing 
            """
            if self.state == STATE_INITIAL:
                logger.debug('{} : request snapshot'.format(self._id))
                self.snapshot.send(b"SNAPSHOT_REQUEST")
                self.state = STATE_SYNCING
            

            """NET IN 
                Given the net state we do something:
                SYNCING : Ask for snapshots
                ACTIVE : Do nothing 
            """
            items = dict(poller.poll(10))

            if self.snapshot in items:
                if self.state == STATE_SYNCING:
                    datablock = ReplicatedDatablock.pull(self.snapshot, self._factory)

                    if datablock.buffer == 'SNAPSHOT_END':
                        self.state = STATE_ACTIVE
                        logger.debug('{} : snapshot done'.format(self._id))



            # We receive updates from the server !
            if self.subscriber in items:
                if self.state == STATE_ACTIVE:
                    logger.debug("{} : Receiving changes from server".format(self._id))
                    datablock = ReplicatedDatablock.pull(self.subscriber, self._factory)
                    datablock.store(self._store_reference)

            if not items:
                logger.error("No request ")
                

            time.sleep(1)
    
    def setup(self,id="Client"):
        pass

    def stop(self):
        self._exit_event.set()

        self.snapshot.close()
        self.subscriber.close()
        self.publish.close()

        self.state = 0



class Server():
    def __init__(self,config=None, factory=None):
        self._rep_store = {}
        self._net = ServerNetService(store_reference=self._rep_store, factory=factory)

    def serve(self):
        self._net.start()

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

        self.bind_ports()

    def bind_ports(self):
        try:
            # Update request
            self.snapshot = self.context.socket(zmq.ROUTER)
            self.snapshot.setsockopt(zmq.IDENTITY, b'SERVER')
            self.snapshot.setsockopt(zmq.RCVHWM, 60)
            self.snapshot.bind("tcp://*:5560")

            # Update all clients
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.setsockopt(zmq.SNDHWM, 60)
            self.publisher.bind("tcp://*:5561")
            time.sleep(0.2)

            # Update collector
            self.pull = self.context.socket(zmq.PULL)
            self.pull.setsockopt(zmq.RCVHWM, 60)
            self.pull.bind("tcp://*:5562")
            
        except zmq.error.ZMQError:
            logger.error("Address already in use, change net config")
    

    def run(self):
        logger.debug("Server is online")
        poller = zmq.Poller()
        poller.register(self.snapshot, zmq.POLLIN)
        poller.register(self.pull, zmq.POLLIN)

        self.state = STATE_ACTIVE

        while not self._exit_event.is_set():
            # Non blocking poller
            socks = dict(poller.poll(10))

            # Snapshot system for late join (Server - Client)
            if self.snapshot in socks:
                msg = self.snapshot.recv_multipart(zmq.DONTWAIT)

                identity = msg[0]
                request = msg[1]

                if request == b"SNAPSHOT_REQUEST":
                    pass
                else:
                    logger.info("Bad snapshot request")
                    break

                for key, item in self._rep_store:
                    self.snapshot.send(identity, zmq.SNDMORE)
                    item.push(self.snapshot)
                
                self.snapshot.send(identity, zmq.SNDMORE)
                RepCommand(owner='server',data='SNAPSHOT_END').push(self.snapshot)
                

                # ordered_props = [(SUPPORTED_TYPES.index(k.split('/')[0]),k,v) for k, v in self.property_map.items()]
                # ordered_props.sort(key=itemgetter(0))

                # for i, k, v in ordered_props:
                #     logger.info(
                #         "Sending {} snapshot to {}".format(k, identity))
                #     self.request_sock.send(identity, zmq.SNDMORE)
                #     v.send(self.request_sock)

                # msg_end_snapshot = message.Message(key="SNAPSHOT_END", id=identity)
                # self.request_sock.send(identity, zmq.SNDMORE)
                # msg_end_snapshot.send(self.request_sock)
                # logger.info("done")

            # Regular update routing (Clients / Client)
            if self.pull in socks:
                logger.debug("Receiving changes from client")
                datablock = ReplicatedDatablock.pull(self.pull, self.factory)

                datablock.store(self._rep_store)
                
                # Update all clients
                datablock.push(self.publisher)
    

    def stop(self):
        self._exit_event.set()

        self.snapshot.close()
        self.pull.close()
        self.publisher.close()

        self.state = 0