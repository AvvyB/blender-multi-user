import threading
import logging
import zmq
import time

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class Client(object):
    def __init__(self):
        self.rep_store = {}
        self.net = ClientNetService(self.rep_store)

    def connect(self):
        self.net.run()
    
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

        self.publish = self.context.socket(zmq.PULL)
        self.publish.bind("tcp://*:5562")

        # For teststing purpose


    def run(self):
        log.debug("Running Net service")

        poller = zmq.Poller()
        poller.register(self.snapshot, zmq.POLLIN)
        poller.register(self.subscriber, zmq.POLLIN)
        poller.register(self.publish, zmq.POLLOUT)

        while not self.exit_event.is_set():
            items = dict(poller.poll(10))

            if not items:
                log.error("No request ")


    def stop(self):
        self.exit_event.set()

        #Wait the end of the run
        while self.exit_event.is_set():
            time.sleep(.1)


