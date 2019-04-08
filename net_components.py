import collections
import logging
import threading
from uuid import uuid4
import binascii
import os
from random import randint
import time
from enum import Enum

try:
    from .libs import umsgpack, zmq
except:
    from libs import umsgpack, zmq
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


class RCFStore(collections.MutableMapping, dict):

    def __init__(self):
        super().__init__()

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)

    def __iter__(self):
        return dict.__iter__(self)

    def __len__(self):
        return dict.__len__(self)

    def __contains__(self, x):
        return dict.__contains__(self, x)


class RCFMessage(object):
    """
    Message is formatted on wire as 2 frames:
    frame 0: key (0MQ string) // property path
    frame 1: id (0MQ string) // property path
    frame 2: mtype (0MQ string) // property path
    frame 3: body (blob) // Could be any data 

    """
    key = None  # key (string)
    id = None  # User  (string)
    mtype = None  # data mtype (string)
    body = None  # data blob
    uuid = None

    def __init__(self,  key=None, uuid=None, id=None, mtype=None, body=None):
        if uuid is None:
            uuid = uuid4().bytes

        self.key = key
        self.uuid = uuid
        self.mtype = mtype
        self.body = body
        self.id = id

    def store(self, dikt):
        """Store me in a dict if I have anything to store"""
        # this currently erasing old value
        if self.key is not None:
            dikt[self.key] = self
        # elif self.key in dikt:
        #     del dikt[self.key]

    def send(self, socket):
        """Send key-value message to socket; any empty frames are sent as such."""
        key = ''.encode() if self.key is None else self.key.encode()
        mtype = ''.encode() if self.mtype is None else self.mtype.encode()
        body = ''.encode() if self.body is None else umsgpack.packb(self.body)
        id = ''.encode() if self.id is None else self.id

        try:
            socket.send_multipart([key, id, mtype, body])
        except:
            logger.info("Fail to send {} {}".format(key,id))

    @classmethod
    def recv(cls, socket):
        """Reads key-value message from socket, returns new kvmsg instance."""
        key, id, mtype, body = socket.recv_multipart(zmq.DONTWAIT)
        key = key.decode() if key else None
        id = id if id else None
        mtype = mtype.decode() if body else None
        body = umsgpack.unpackb(body) if body else None

        return cls(key=key, id=id, mtype=mtype, body=body)

    def dump(self):
        if self.body is None:
            size = 0
            data = 'NULL'
        else:
            size = len(self.body)
            data = repr(self.body)
        print("[key:{key}][size:{size}][mtype:{mtype}] {data}".format(
            key=self.key,
            size=size,
            mtype=self.mtype,
            data=data,
        ))


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

    def connect(self, address, port):
        self.pipe.send_multipart([b"CONNECT", (address.encode() if isinstance(
            address, str) else address), b'%d' % port])

    def set(self, key, value):
        """Set new value in distributed hash table
        Sends [SET][key][value][ttl] to the agent
        """
        self.pipe.send_multipart([b"SET", umsgpack.packb(key), umsgpack.packb(value)])

    def exit(self):
        if self.agent.is_alive():
            global stop
            stop = True

class RCFServer(object):
    address = None          # Server address
    port = None             # Server port
    snapshot = None         # Snapshot socket
    subscriber = None       # Incoming updates

    def __init__(self, ctx, address, port,id):
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
        self.property_map = RCFStore()
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
            address = msg.pop(0)
            port = int(msg.pop(0))

            if self.server is None:
                self.server = RCFServer(self.ctx, address, port, self.id)
                self.publisher.connect("tcp://{}:{}".format(address.decode(), port+2))

            else:
                logger.error("E: too many servers (max. %i)", SERVER_MAX)
       
        elif command == b"SET":
            key,value = msg

            # Send key-value pair on to server
            rcfmsg = RCFMessage(key=umsgpack.unpackb(key),id=self.id ,mtype="",body=umsgpack.unpackb(value))
            rcfmsg.store(self.property_map)
            
            rcfmsg.send(self.publisher)

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
                logger.info("I: waiting for server at %s:%d...",
                            server.address, server.port)
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
            pass

        if agent.pipe in items:
            agent.control_message()
        elif server_socket in items:
            rcfmsg = RCFMessage.recv(server_socket)
            if agent.state == State.SYNCING:
                # Store snapshot
                if rcfmsg.key == "SNAPSHOT_END":
                    logger.info("snapshot complete")
                    agent.state = State.ACTIVE
                else:
                    rcfmsg.store(agent.property_map)
            elif agent.state == State.ACTIVE:
                if rcfmsg.id != agent.id:
                    rcfmsg.store(agent.property_map)
                    action = "update" if rcfmsg.body else "delete"
                    logging.info("I: received from {}:{},{} {}".format(server.address,rcfmsg.body.id, server.port, action))
                else:
                    logger.info("IDLE")

    logger.info("exit thread")
    stop = False
        # else: else
        #     agent.state = State.INITIAL

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

                msg_end_snapshot = RCFMessage(key="SNAPSHOT_END", id=identity)
                self.request_sock.send(identity, zmq.SNDMORE)
                msg_end_snapshot.send(self.request_sock)
                logger.info("done")

            # Regular update routing (Clients / Client)
            elif self.collector_sock in socks:
                msg  = RCFMessage.recv(self.collector_sock)
                # Update all clients
                msg.store(self.property_map)
                msg.send(self.pub_sock)
            
