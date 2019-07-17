import threading
import logging
import zmq
import time
from replication import ReplicatedDatablock

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

STATE_INITIAL = 0
STATE_SYNCING = 1
STATE_ACTIVE = 2


class Client(object):
    def __init__(self,factory=None, config=None):
        self._rep_store = {}
        self._net = ClientNetService(self._rep_store)
        assert(factory)
        self._factory = factory

    def connect(self):
        self._net.start()

    def disconnect(self):
        self._net.stop()

    def register(self, object):
        """
        Register a new item for replication
        """
        assert(object)
        
        new_item = self._factory.construct_from_dcc(object)(owner="client")

        if new_item:
            log.info("Registering {} on {}".format(object,new_item.uuid))
            new_item.store(self._rep_store)
            
            log.info("Pushing changes...")
            new_item.push(self._net.publish)
            return new_item.uuid
        else:
            raise TypeError("Type not supported")

    def pull(self,object=None):
        pass
    

    def unregister(self,object):
        pass
    
    
    
class ClientNetService(threading.Thread):
    def __init__(self,store_reference=None):
        # Threading
        threading.Thread.__init__(self)
        self.name = "ClientNetLink"
        self.daemon = True
        self.exit_event = threading.Event()

        # Networking
        self.context = zmq.Context.instance()

        self.snapshot = self.context.socket(zmq.DEALER)
        self.snapshot.connect("tcp://127.0.0.1:5560")
        
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, '')
        self.subscriber.connect("tcp://127.0.0.1:5561")
        self.subscriber.linger = 0

        self.publish = self.context.socket(zmq.PUSH)
        self.publish.connect("tcp://127.0.0.1:5562")

        self.state = STATE_INITIAL


    def run(self):
        log.info("Client is listening")
        poller = zmq.Poller()
        poller.register(self.snapshot, zmq.POLLIN)
        poller.register(self.subscriber, zmq.POLLIN)
        poller.register(self.publish, zmq.POLLOUT)

        self.state = 1

        while not self.exit_event.is_set():
            items = dict(poller.poll(10))

            if not items:
                log.error("No request ")

            time.sleep(1)
    

    def stop(self):
        self.exit_event.set()

        self.snapshot.close()
        self.subscriber.close()
        self.publish.close()

        self.state = 0



class Server():
    def __init__(self,config=None):
        self.rep_store = {}
        self.net = ServerNetService(self.rep_store)
        # self.serve()

    def serve(self):
        self.net.start()

    def state(self):
        return self.net.state

    def stop(self):
        self.net.stop()


class ServerNetService(threading.Thread):
    def __init__(self,store_reference=None, factory=None):
        # Threading
        threading.Thread.__init__(self)
        self.name = "ServerNetLink"
        self.daemon = True
        self.exit_event = threading.Event()
        self.store =  store_reference

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
            log.error("Address already in use, change net config")
    

    def run(self):
        log.info("Server is listening")
        poller = zmq.Poller()
        poller.register(self.snapshot, zmq.POLLIN)
        poller.register(self.pull, zmq.POLLIN)

        self.state = STATE_ACTIVE

        while not self.exit_event.is_set():
            # Non blocking poller
            socks = dict(poller.poll(1000))

            # Snapshot system for late join (Server - Client)
            # if self.snapshot in socks:
                # msg = self.snapshot.recv_multipart(zmq.DONTWAIT)

                # identity = msg[0]
                # request = msg[1]

                # if request == b"SNAPSHOT_REQUEST":
                #     pass
                # else:
                #     logger.info("Bad snapshot request")
                #     break

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
                log.info("Receiving changes from client")
                msg = ReplicatedDatablock.pull(self.pull)

                msg.store(self.store)
                # msg = message.Message.recv(self.collector_sock)
                # # logger.info("received object")
                # # Update all clients
                # msg.store(self.store)
                # msg.send(self.pub_sock)
    

    def stop(self):
        self.exit_event.set()

        self.snapshot.close()
        self.pull.close()
        self.publisher.close()

        self.state = 0