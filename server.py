import logging
import time 
import environment
from operator import itemgetter


import zmq
import message

logger = logging.getLogger("Server")
logging.basicConfig(level=logging.DEBUG)

SUPPORTED_TYPES = ['Client','Curve','Material','Texture', 'Light', 'Camera', 'Mesh','Armature', 'GreasePencil', 'Object', 'Action', 'Collection', 'Scene']
                   
class ServerAgent():
    def __init__(self, context=zmq.Context.instance(), id="admin"):
        self.context = context
        self.config = environment.load_config()
        self.port = int(self.config['port']) if "port" in self.config.keys() else 5555
        self.pub_sock = None
        self.request_sock = None
        self.collector_sock = None
        self.poller = None

        self.property_map = {}
        self.id = id
        self.bind_ports()
        # Main client loop registration
        self.tick()

        logger.info("{} client initialized".format(id))

    def bind_ports(self):
        # Update all clients
        self.pub_sock = self.context.socket(zmq.PUB)
        self.pub_sock.setsockopt(zmq.SNDHWM, 60)
        self.pub_sock.bind("tcp://*:"+str(self.port+1))
        time.sleep(0.2)

        # Update request
        self.request_sock = self.context.socket(zmq.ROUTER)
        self.request_sock.setsockopt(zmq.IDENTITY, b'SERVER')
        self.request_sock.setsockopt(zmq.RCVHWM, 60)
        self.request_sock.bind("tcp://*:"+str(self.port))

        # Update collector
        self.collector_sock = self.context.socket(zmq.PULL)
        self.collector_sock.setsockopt(zmq.RCVHWM, 60)
        self.collector_sock.bind("tcp://*:"+str(self.port+2))

        # poller for socket aggregation
        self.poller = zmq.Poller()
        self.poller.register(self.request_sock, zmq.POLLIN)
        self.poller.register(self.collector_sock, zmq.POLLIN)

    def tick(self):
        logger.info("{} server launched".format(id))

        while True:
            # Non blocking poller
            socks = dict(self.poller.poll(1000))

            # Snapshot system for late join (Server - Client)
            if self.request_sock in socks:
                msg = self.request_sock.recv_multipart(zmq.DONTWAIT)

                identity = msg[0]
                request = msg[1]

                if request == b"SNAPSHOT_REQUEST":
                    pass
                else:
                    logger.info("Bad snapshot request")
                    break

                ordered_props = [(SUPPORTED_TYPES.index(k.split('/')[0]),k,v) for k, v in self.property_map.items()]
                ordered_props.sort(key=itemgetter(0))

                for i, k, v in ordered_props:
                    logger.info(
                        "Sending {} snapshot to {}".format(k, identity))
                    self.request_sock.send(identity, zmq.SNDMORE)
                    v.send(self.request_sock)

                msg_end_snapshot = message.Message(key="SNAPSHOT_END", id=identity)
                self.request_sock.send(identity, zmq.SNDMORE)
                msg_end_snapshot.send(self.request_sock)
                logger.info("done")

            # Regular update routing (Clients / Client)
            elif self.collector_sock in socks:
                msg = message.Message.recv(self.collector_sock)
                # logger.info("received object")
                # Update all clients
                msg.store(self.property_map)
                msg.send(self.pub_sock)

server = ServerAgent()

