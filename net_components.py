import zmq
import asyncio
import logging
from .libs import umsgpack
from .libs import kvsimple
import time
import random
import strut

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class RCFMessage():
    """
    Message is formatted on wire as 2 frames:
    frame 0: key (0MQ string) // property path
    frame 2: body (blob)

    """
    key = None # key (string)
    body = None # blob

    def __init__(self, key=None, body=None):
        self.key = key
        self.body = body

    def store(self, dikt):
        """Store me in a dict if I have anything to store"""
        # this seems weird to check, but it's what the C example does
        # this currently erasing old value 
        if self.key is not None and self.body is not None:
            dikt[self.key] = self

    def send(self, socket):
        """Send key-value message to socket; any empty frames are sent as such."""
        key = '' if self.key is None else self.key)
        body = '' if self.body is None else self.body
        socket.send_multipart([ key, body ])

    @classmethod
    def recv(cls, socket):
        """Reads key-value message from socket, returns new kvmsg instance."""
        key, body = socket.recv_multipart()
        key = key if key else None
        body = body if body else None
        return cls(key=key, body=body)

    def dump(self):
        if self.body is None:
            size = 0
            data='NULL'
        else:
            size = len(self.body)
            data=repr(self.body)
        print("[key:{key}][size:{size}] {data}".format(
            key=self.key,
            size=size,
            data=data,
        ))

class Client():
    def __init__(self, context=zmq.Context(), id="default", recv_callback=None):
        self.context = context
        self.pull_sock = None
        self.push_sock = None
        self.poller = None

        self.id = id
        self.recv_callback = recv_callback
        self.bind_ports()
        # Main client loop registration
        self.task = asyncio.ensure_future(self.main())

        self.property_map = {}
        self.store = []
        logger.info("{} client initialized".format(id))

    def bind_ports(self):
        # pull socket: get update FROM server
        self.pull_sock = self.context.socket(zmq.SUB)
        self.pull_sock.linger = 0
        self.pull_sock.connect("tcp://localhost:5555")
        self.pull_sock.setsockopt_string(zmq.SUBSCRIBE, '')

        # push socket: push update TO server
        self.push_sock = self.context.socket(zmq.DEALER)
        self.push_sock.setsockopt(zmq.IDENTITY, self.id.encode())
        self.push_sock.linger = 0
        self.push_sock.connect("tcp://localhost:5556")

        # Sockets aggregator, not really used for now
        self.poller = zmq.Poller()
        self.poller.register(self.pull_sock, zmq.POLLIN)

    async def main(self):
        logger.info("{} client launched".format(id))

       # Prepare our context and publisher socket
        while True:
            # TODO: find a better way
            await asyncio.sleep(0.016)
            try:
                socks = dict(self.poller.poll(1))
            except KeyboardInterrupt:
                break

            if self.pull_sock in socks:
                message = self.pull_sock.recv_multipart(zmq.NOBLOCK)
                logger.info("{}:{}".format(message[0].decode(
                    'ascii'), umsgpack.unpackb(message[1])))
                # Store message
                self.store.append(
                    [message[0].decode('ascii'), umsgpack.unpackb(message[1])])

                if self.recv_callback:
                    self.recv_callback()

    def send_msg(self, msg):
        self.push_sock.send(umsgpack.packb(msg))

    def stop(self):
        logger.info("Stopping client")
        self.poller.unregister(self.pull_sock)
        self.push_sock.close()
        self.pull_sock.close()
        self.task.cancel()


class Server():
    def __init__(self, context=zmq.Context(), id="admin"):
        self.context = context
        self.pub_sock = None
        self.pull_sock = None
        self.poller = None

        self.id = id
        self.bind_ports()
        # Main client loop registration
        self.task = asyncio.ensure_future(self.main())

        logger.info("{} client initialized".format(id))

    def bind_ports(self):
        # Update all clients
        self.pub_sock = self.context.socket(zmq.PUB)
        self.pub_sock.bind("tcp://*:5555")
        time.sleep(0.2)

        # Update receiver
        self.pull_sock = self.context.socket(zmq.ROUTER)
        self.pull_sock.bind("tcp://*:5556")

        # poller for socket aggregation
        self.poller = zmq.Poller()
        self.poller.register(self.pull_sock, zmq.POLLIN)

    async def main(self):
        logger.info("{} server launched".format(id))
        # Prepare our context and publisher socket
        while True:
            # TODO: find a better way
            await asyncio.sleep(0.016)

            try:
                socks = dict(self.poller.poll(1))
            except KeyboardInterrupt:
                break

            if self.pull_sock in socks:
                msg = self.pull_sock.recv_multipart(zmq.NOBLOCK)
                #print("{}:{}".format(msg[0].decode('ascii'), umsgpack.packb(msg[1])))

                # Update all clients
                self.pub_sock.send_multipart(msg)

    def stop(self):
        logger.info("Stopping server")
        self.poller.unregister(self.pull_sock)
        self.pub_sock.close()
        self.pull_sock.close()

        self.task.cancel()
