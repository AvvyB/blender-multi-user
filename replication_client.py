import threading
import logging
import zmq
import time
import replication

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

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

        new_item = self._factory.construct(object)(owner="client")
        new_item.store(self._rep_store)

        return new_item.uuid

    def get(self,object=None):
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

        self.state = 0


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
    
    def send(data):
        assert(issubclass(data, ReplicatedDatablock))
        data.push(self.publish)

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
    def __init__(self,store_reference=None):
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

        self.state = 1

        while not self.exit_event.is_set():
            items = dict(poller.poll(10))

            if not items:
               pass

            time.sleep(.1)
    
    def stop(self):
        self.exit_event.set()

        self.snapshot.close()
        self.pull.close()
        self.publisher.close()

        self.state = 0