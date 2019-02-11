import zmq
import asyncio
import logging
from .libs import umsgpack
from .libs import kvsimple
import time
import random


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class Session():
    def __init__(self, host='127.0.0.1', port=5555, is_hosting=False):
        self.host = host
        self.port = port
        self.is_running = False
        # init zmq context
        self.context = zmq.Context()
        self.socket = None

        self.msg = []

        # self.listen.add_done_callback(self.close_success())

    # TODO: Add a kill signal to destroy clients session
    # TODO: Add a join method
    # TODO: Add a create session method
    def join(self):
        logger.info("joinning  {}:{}".format(self.host, self.port))
        try:
            self.socket = self.context.socket(zmq.DEALER)
            self.socket.connect("tcp://localhost:5555")
            self.listen = asyncio.ensure_future(self.listen())

            self.send("XXX connected")
            return True

        except zmq.ZMQError:
            logger.error("Error while joining  {}:{}".format(
                self.host, self.port))

        return False

    # TODO: Find better names
    def create(self):
        logger.info("Creating session")
        try:
            self.socket = self.context.socket(zmq.ROUTER)
            self.socket.bind("tcp://*:5555")

            self.listen = asyncio.ensure_future(self.listen())
            return True
        except zmq.ZMQError:
            logger.error("Error while creating session: ", zmq.ZMQError)

        return False

    async def listen(self):
        logger.info("Listening on {}:{}".format(self.host, self.port))

        self.is_running = True
        while True:
            # Ungly blender workaround to prevent blocking...
            await asyncio.sleep(0.016)
            try:
                buffer = self.socket.recv(zmq.NOBLOCK)

                message = umsgpack.unpackb(buffer)
                if message is not 0:
                    self.socket.send(umsgpack.packb(0))
                    self.msg.append()
            except zmq.ZMQError:
                pass

    def send(self, msg):
        logger.info("Sending {} to {}:{} ".format(msg, self.host, self.port))
        self.msg.append(msg)
        bin = umsgpack.packb(msg)
        self.socket.send(bin)

    async def close_success(self):
        self.is_running = False

    def close(self):
        logger.info("Closing session")
        self.socket.close()
        self.listen.cancel()
        del self.listen
        self.is_running = False



class Client():
    def __init__(self, context=zmq.Context(), id="default"):

        self.context = context
        self.pull_sock = None
        self.push_sock = None
        self.poller = None
        
        self.id = id
        self.bind_ports()
        # Main client loop registration
        self.is_running = False
        self.task = asyncio.ensure_future(self.main())

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
        self.is_running = True
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
                logger.info("{}:{}".format(message[0].decode('ascii'), umsgpack.unpackb(message[1])))
                # Store message
                self.store.append([message[0].decode('ascii'), umsgpack.unpackb(message[1])])

    def send_msg(self, msg):
        self.push_sock.send(umsgpack.packb(msg))

    def stop(self):
        logger.info("Stopping client")
        self.is_running = False
        self.task.cancel()
        self.push_sock.close()
        self.pull_sock.close()
        self.context.term()


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
        self.task.cancel()
        self.pub_sock.close()
        self.pull_sock.close()
        self.context.term()
