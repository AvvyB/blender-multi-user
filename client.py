import binascii
import collections
import logging
import os
import sys
import threading
import time
from enum import Enum
from random import randint
from uuid import uuid4



try:
    from .libs import umsgpack
    from .libs import zmq
    from .libs import dump_anything
    from . import helpers
    from . import message
except:
    # Server import
    from libs import umsgpack
    from libs import zmq
    from libs import dump_anything
    import helpers
    import message

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

CONNECT_TIMEOUT = 2
WAITING_TIME = 0.001
SERVER_MAX = 1

stop = False


def zpipe(ctx):
    """build inproc pipe for talking to threads

    mimic pipe used in czmq zthread_fork.

    Returns a pair of PAIRs connected via inproc
    """
    a = ctx.socket(zmq.PAIR)
    b = ctx.socket(zmq.PAIR)
    a.linger = b.linger = 0
    a.hwm = b.hwm = 1
    iface = "inproc://%s" % binascii.hexlify(os.urandom(8))
    a.bind(iface)
    b.connect(iface)
    return a, b


class State(Enum):
    INITIAL = 1
    SYNCING = 2
    ACTIVE = 3



class RCFClient(object):
    ctx = None
    pipe = None
    agent = None

    def __init__(self):
        self.ctx = zmq.Context()
        self.pipe, peer = zpipe(self.ctx)
        self.agent = threading.Thread(
            target=rcf_client_agent, args=(self.ctx, peer))
        self.agent.daemon = True
        self.agent.start()

    def connect(self, id, address, port):
        self.pipe.send_multipart([b"CONNECT", (id.encode() if isinstance(
            id, str) else id), (address.encode() if isinstance(
            address, str) else address), b'%d' % port])

    def set(self, key):
        """Set new value in distributed hash table
        Sends [SET][key][value] to the agent
        """
        self.pipe.send_multipart(
            [b"SET", umsgpack.packb(key)])

    def get(self, key):
        """Lookup value in distributed hash table
        Sends [GET][key] to the agent and waits for a value response
        If there is no clone available, will eventually return None.
        """

        self.pipe.send_multipart([b"GET", umsgpack.packb(key)])
        try:
            reply = self.pipe.recv_multipart()
        except KeyboardInterrupt:
            return
        else:
            return umsgpack.unpackb(reply[0])

    def exit(self):
        if self.agent.is_alive():
            global stop
            stop = True

    def list(self):
        self.pipe.send_multipart([b"LIST"])
        try:
            reply = self.pipe.recv_multipart()
        except KeyboardInterrupt:
            return
        else:
            return umsgpack.unpackb(reply[0])

class RCFServer(object):
    address = None          # Server address
    port = None             # Server port
    snapshot = None         # Snapshot socket
    subscriber = None       # Incoming updates

    def __init__(self, ctx, address, port, id):
        self.address = address
        self.port = port
        self.snapshot = ctx.socket(zmq.DEALER)
        self.snapshot.linger = 0
        self.snapshot.connect("tcp://{}:{}".format(address.decode(), port))
        self.snapshot.setsockopt(zmq.IDENTITY, id)
        self.subscriber = ctx.socket(zmq.SUB)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, '')
        self.subscriber.connect("tcp://{}:{}".format(address.decode(), port+1))
        self.subscriber.linger = 0
        print("connected on tcp://{}:{}".format(address.decode(), port))


class RCFClientAgent(object):
    ctx = None
    pipe = None
    property_map = None
    publisher = None
    id = None
    state = State.INITIAL
    server = None

    def __init__(self, ctx, pipe):
        self.ctx = ctx
        self.pipe = pipe
        self.property_map = {}
        self.id = b"test"
        self.state = State.INITIAL
        self.server = None
        self.publisher = self.ctx.socket(zmq.PUSH)  # push update socket
        self.publisher.setsockopt(zmq.IDENTITY, self.id)
        self.publisher.setsockopt(zmq.SNDHWM, 60)
        self.publisher.linger = 0

    def control_message(self):
        msg = self.pipe.recv_multipart()
        command = msg.pop(0)

        if command == b"CONNECT":
            self.id = msg.pop(0)
            address = msg.pop(0)
            port = int(msg.pop(0))

            if self.server is None:
                self.server = RCFServer(self.ctx, address, port, self.id)
                self.publisher.connect(
                    "tcp://{}:{}".format(address.decode(), port+2))

            else:
                logger.error("E: too many servers (max. %i)", SERVER_MAX)

        elif command == b"SET":
            key = umsgpack.unpackb(msg[0])
            value = None
            value = helpers.dump(key)
           
            if value:
                logger.info("{} dumped".format(key))
                # Send key-value pair on to server
                rcfmsg = message.RCFMessage(key=key, id=self.id, mtype="", body=value)

                rcfmsg.store(self.property_map)
                rcfmsg.send(self.publisher)
            else:
                logger.error("Fail to dump ")

        elif command == b"GET":
            key = umsgpack.unpackb(msg[0])
            value = self.property_map.get(key)
            self.pipe.send(umsgpack.packb(value.body) if value else b'')
        
        elif command == b"LIST":
            self.pipe.send(umsgpack.packb(list(self.property_map)))
  

def rcf_client_agent(ctx, pipe):
    agent = RCFClientAgent(ctx, pipe)
    server = None
    global stop
    while True:
        if stop:
            break
        # logger.info("asdasd")
        poller = zmq.Poller()
        poller.register(agent.pipe, zmq.POLLIN)
        server_socket = None

        if agent.state == State.INITIAL:
            server = agent.server
            if agent.server:
                logger.info("%s: waiting for server at %s:%d...",
                            agent.id.decode(),server.address, server.port)
                server.snapshot.send(b"SNAPSHOT_REQUEST")
                agent.state = State.SYNCING
                server_socket = server.snapshot
        elif agent.state == State.SYNCING:
            server_socket = server.snapshot
        elif agent.state == State.ACTIVE:
            server_socket = server.subscriber

        if server_socket:
            poller.register(server_socket, zmq.POLLIN)

        try:
            items = dict(poller.poll(1))
        except:
            raise
            break

        if agent.pipe in items:
            agent.control_message()
        elif server_socket in items:
            rcfmsg = message.RCFMessage.recv(server_socket)
            if agent.state == State.SYNCING:
                # Store snapshot
                if rcfmsg.key == "SNAPSHOT_END":
                    # logger.info("snapshot complete")
                    agent.state = State.ACTIVE
                else:
                    helpers.load(rcfmsg.key,rcfmsg.body)
                    rcfmsg.store(agent.property_map)
            elif agent.state == State.ACTIVE:
                if rcfmsg.id != agent.id:
                    helpers.load(rcfmsg.key,rcfmsg.body)
                    # logger.info("load")
                    rcfmsg.store(agent.property_map)
                    # action = "update" if rcfmsg.body else "delete"
                    # logging.info("{}: received from {}:{},{} {}".format(rcfmsg.key,
                    #     server.address, rcfmsg.id, server.port, action))
                else:
                    logger.info("{} nothing to do".format(agent.id))

    logger.info("exit thread")
    stop = False
    # else: else
    #     agent.state = State.INITIAL


class SerializationAgent(object):
    ctx = None
    pipe = None

    def __init__(self, ctx, pipe_in, pipe_out):
        self.ctx = ctx
        self.pipe_in = pipe_in
        self.pipe_out = pipe_out

    def control_message(self):
        msg = self.pipe_in.recv_multipart()
        command = msg.pop(0)

        if command == b"DUMP":
            key = umsgpack.unpackb(msg[0])

            logger.log("Dumping....")

        elif command == b"LOAD":
            key, value = msg
            logger.log("Loading....")


def serialization_agent(ctx, pipe_in, pipe_out):
    agent = SerializationAgent(ctx, pipe_in, pipe_out)
    server = None

    global stop
    while True:
        if stop:
            break

        poller = zmq.Poller()
        poller.register(agent.pipe, zmq.POLLIN)

        try:
            items = dict(poller.poll(1))
        except:
            raise
            break

        if agent.pipe in items:
            agent.control_message()

