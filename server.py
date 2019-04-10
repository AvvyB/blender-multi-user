import logging
import time 

from libs import zmq

import message
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class RCFServerAgent():
    def __init__(self, context=zmq.Context.instance(), id="admin"):
        self.context = context

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
        self.pub_sock.bind("tcp://*:5556")
        time.sleep(0.2)

        # Update request
        self.request_sock = self.context.socket(zmq.ROUTER)
        self.request_sock.setsockopt(zmq.IDENTITY, b'SERVER')
        self.request_sock.setsockopt(zmq.RCVHWM, 60)
        self.request_sock.bind("tcp://*:5555")

        # Update collector
        self.collector_sock = self.context.socket(zmq.PULL)
        self.collector_sock.setsockopt(zmq.RCVHWM, 60)
        self.collector_sock.bind("tcp://*:5557")

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
                print("asdasd")
                if request == b"SNAPSHOT_REQUEST":
                    pass
                else:
                    logger.info("Bad snapshot request")
                    break

                for k, v in self.property_map.items():
                    logger.info(
                        "Sending {} snapshot to {}".format(k, identity))
                    self.request_sock.send(identity, zmq.SNDMORE)
                    v.send(self.request_sock)

                msg_end_snapshot = message.RCFMessage(key="SNAPSHOT_END", id=identity)
                self.request_sock.send(identity, zmq.SNDMORE)
                msg_end_snapshot.send(self.request_sock)
                logger.info("done")

            # Regular update routing (Clients / Client)
            elif self.collector_sock in socks:
                msg = message.RCFMessage.recv(self.collector_sock)
                # Update all clients
                msg.store(self.property_map)
                msg.send(self.pub_sock)

server = RCFServerAgent()

