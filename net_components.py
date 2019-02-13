import zmq
import asyncio
import logging
from .libs import umsgpack
import time
import random
import struct

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


# TODO: Add message time and author stamp for reliabilty
class RCFMessage(object):
    """
    Message is formatted on wire as 2 frames:
    frame 0: key (0MQ string) // property path
    frame 2: body (blob) // Could be any data 

    """
    key = None  # key (string)
    body = None  # blob

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
        key = '' if self.key is None else self.key.encode()
        body = '' if self.body is None else umsgpack.packb(self.body)
        socket.send_multipart([key, body])

    @classmethod
    def recv(cls, socket):
        """Reads key-value message from socket, returns new kvmsg instance."""
        key, body = socket.recv_multipart(zmq.NOBLOCK)
        key =  key.decode() if key else None
        body = umsgpack.unpackb(body) if body else None
 
        return cls(key=key, body=body)

    def dump(self):
        if self.body is None:
            size = 0
            data = 'NULL'
        else:
            size = len(self.body)
            data = repr(self.body)
        print("[key:{key}][size:{size}] {data}".format(
            key=self.key,
            size=size,
            data=data,
        ))


class Client():
    def __init__(self, context=zmq.Context(), id="default", recv_callback=None):
        self.context = context
        self.pull_sock = None
        self.req_sock = None
        self.poller = None

        self.id = id.encode()
        self.recv_callback = recv_callback
        self.bind_ports()
        # Main client loop registration
        self.task = asyncio.ensure_future(self.main())

        self.property_map = {}
        
        logger.info("{} client initialized".format(id))

    def bind_ports(self):
        # pull socket: get update FROM server
        self.pull_sock = self.context.socket(zmq.SUB)
        self.pull_sock.linger = 0
        self.pull_sock.connect("tcp://localhost:5555")
        self.pull_sock.setsockopt_string(zmq.SUBSCRIBE, '')

        # request socket: send request/message over all peers throught the server
        self.req_sock = self.context.socket(zmq.DEALER)
        self.req_sock.setsockopt(zmq.IDENTITY, self.id)
        self.req_sock.linger = 0
        self.req_sock.connect("tcp://localhost:5556")

        # push update socket
        self.push_sock = self.context.socket(zmq.PUSH)
        self.push_sock.setsockopt(zmq.IDENTITY, self.id)
        self.push_sock.linger = 0
        self.push_sock.connect("tcp://localhost:5557")

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
                rcfmsg = RCFMessage.recv(self.pull_sock)

                rcfmsg.store(self.property_map)
                rcfmsg.dump()
                
                for f in self.recv_callback:
                    f(rcfmsg)

    def push_update(self, key, body):
        rcfmsg = RCFMessage(key,body)
        rcfmsg.send(self.push_sock)
        # self.push_sock.send_multipart()

    def stop(self):
        logger.info("Stopping client")
        self.poller.unregister(self.pull_sock)
        self.req_sock.close()
        self.push_sock.close()
        self.pull_sock.close()
        self.task.cancel()


class Server():
    def __init__(self, context=zmq.Context(), id="admin"):
        self.context = context

        self.pub_sock = None
        self.request_sock = None
        self.collector_sock = None
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

        # Update request
        self.request_sock = self.context.socket(zmq.ROUTER)
        self.request_sock.bind("tcp://*:5556")

        # Update collector
        self.collector_sock = self.context.socket(zmq.PULL)
        self.collector_sock.bind("tcp://*:5557")

        # poller for socket aggregation
        self.poller = zmq.Poller()
        self.poller.register(self.request_sock, zmq.POLLIN)
        self.poller.register(self.collector_sock, zmq.POLLIN)

    async def main(self):
        logger.info("{} server launched".format(id))

        while True:
            # TODO: find a better way
            await asyncio.sleep(0.016)

            try:
                socks = dict(self.poller.poll(1))
            except KeyboardInterrupt:
                break

            if self.request_sock in socks:
                msg = self.request_sock.recv_multipart(zmq.NOBLOCK)

                # Update all clients
                self.pub_sock.send_multipart(msg)

            if self.collector_sock in socks:
                msg = self.collector_sock.recv_multipart(zmq.NOBLOCK)

                # Update all clients
                self.pub_sock.send_multipart(msg)

    def stop(self):
        logger.info("Stopping server")
        self.poller.unregister(self.request_sock)
        self.pub_sock.close()
        self.request_sock.close()
        self.collector_sock.close()
        self.task.cancel()
