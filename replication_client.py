import threading
import logging
import zmq
import time
import replication

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class Client(object):
    def __init__(self,factory=None, config=None):
        self.rep_store = {}
        self.net = ClientNetService(self.rep_store)
        self.factory = factory

    def connect(self):
        self.net.start()

    def replicate(self, object):
        new_item = self.factory.construct(object)(owner="client")

        new_item.store(self.rep_store)

    def state(self):
        return self.net.state

    def stop(self):
        self.net.stop()
    
class ClientNetService(threading.Thread):
    def __init__(self,store_reference=None):
        # Threading
        threading.Thread.__init__(self)
        self.name = "NetLink"
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
        self.name = "NetLink"
        self.daemon = True
        self.exit_event = threading.Event()
        self.store =  store_reference

        self.context = zmq.Context.instance()

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


        self.state = 0

    def run(self):
        poller = zmq.Poller()
        poller.register(self.snapshot, zmq.POLLIN)
        poller.register(self.pull, zmq.POLLIN)

        self.state = 1

        while not self.exit_event.is_set():
            items = dict(poller.poll(10))

            if not items:
               pass

            time.sleep(.1)