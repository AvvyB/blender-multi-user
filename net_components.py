import collections
import logging
from uuid import uuid4
import time
from enum import Enum

from .libs import umsgpack, zmq

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

CONNECT_TIMEOUT = 2
WAITING_TIME = 0.001
SERVER_MAX = 1

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
    return a,b


class State(Enum):
    INITIAL = 1
    SYNCING = 2
    ACTIVE = 3


class RCFFactory(object):
    """
    Abstract layer used to bridge external and inter
    """

    def init(self, data):
        """
        set the RCFMessage pointer to local data
        """
        print("Default setter")
        # Setup data accessor
        data.get = self.load_getter(data)
        data.set = self.load_setter(data)

        # TODO: Setup local pointer

    def load_getter(self, data):
        """
        local program > rcf 

        """
        print("Default getter")
        return None

    def load_setter(self, data):
        """
        rcf > local program
        """
        print("Default setter")
        return None

    def apply(self, data):
        pass

    def diff(self, data):
        """
        Verify data integrity 
        """
        pass


class RCFStore(collections.MutableMapping, dict):

    def __init__(self, custom_factory=RCFFactory()):
        super().__init__()
        self.factory = custom_factory

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

    def __init__(self,  key=None,uuid= None, id=None, mtype=None, body=None):
        if uuid is None:
            uuid = uuid4()
        
        self.key = key
        self.uuid = uuid
        self.mtype = mtype
        self.body = body
        self.id = id

        

    def store(self, dikt):
        """Store me in a dict if I have anything to store"""
        # this currently erasing old value
        if self.key is not None :
            dikt[self.key] = self
        # elif self.key in dikt:
        #     del dikt[self.key]

    def send(self, socket):
        """Send key-value message to socket; any empty frames are sent as such."""
        key = ''.encode() if self.key is None else self.key.encode()
        print(self.mtype)
        mtype = ''.encode() if self.mtype is None else self.mtype.encode()
        body = ''.encode() if self.body is None else umsgpack.packb(self.body)
        id = ''.encode() if self.id is None else self.id

        try:
            socket.send_multipart([key,self.uuid, id, mtype, body])
        except:
            logger.info("Fail to send {}".format(key))

    @classmethod
    def recv(cls, socket):
        """Reads key-value message from socket, returns new kvmsg instance."""
        key,uuid, id, mtype, body = socket.recv_multipart(zmq.DONTWAIT)
        key = key.decode() if key else None
        id = id if id else None
        mtype = mtype.decode() if body else None
        body = umsgpack.unpackb(body) if body else None

        return cls(key=key,uuid=uuid, id=id, mtype=mtype, body=body)

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



class RCFClient():
    def __init__(
            self,
            context=zmq.Context(),
            id="default",
            on_recv=None,
            on_post_init=None,
            is_admin=False,
            factory=None,
            address="localhost"):

        # 0MQ vars
        self.context = context
        self.pull_sock = None
        self.req_sock = None
        self.poller = None

        # Client configuration
        self.id = id.encode()
        self.on_recv = on_recv
        self.on_post_init = on_post_init
        self.status = RCFStatus.IDLE
        self.is_admin = is_admin
        self.address = address

        self.bind_ports()

        # client routine registration
        self.load_task = asyncio.ensure_future(self.load())
        self.tick_task = None

       

        logger.info("{} client initialized".format(id))

    def bind_ports(self):
        # pull socket: get update FROM server
        self.pull_sock = self.context.socket(zmq.SUB)
        self.pull_sock.linger = 0
        self.pull_sock.connect("tcp://{}:5555".format(self.address))
        self.pull_sock.setsockopt_string(zmq.SUBSCRIBE, '')

        # request socket: send request/message over all peers throught the server
        self.req_sock = self.context.socket(zmq.DEALER)
        self.req_sock.setsockopt(zmq.IDENTITY, self.id)
        # self.req_sock.setsockopt(zmq.SNDHWM, 60)
        self.req_sock.linger = 0
        self.req_sock.connect("tcp://{}:5556".format(self.address))

        # push update socket
        self.push_sock = self.context.socket(zmq.PUSH)
        self.push_sock.setsockopt(zmq.IDENTITY, self.id)
        self.push_sock.linger = 0
        self.push_sock.connect("tcp://{}:5557".format(self.address))
        self.push_sock.setsockopt(zmq.SNDHWM, 60)

        # Sockets aggregator, not really used for now
        self.poller = zmq.Poller()
        self.poller.register(self.pull_sock, zmq.POLLIN)

        time.sleep(0.1)


    def push_update(self, key, mtype, body):
        rcfmsg = RCFMessage(key=key, id=self.id,mtype=mtype, body=body)
        rcfmsg.send(self.push_sock)

    def stop(self):
        logger.debug("Stopping client")
        self.poller.unregister(self.pull_sock)
        self.req_sock.close()
        self.push_sock.close()
        self.pull_sock.close()
        self.load_task.cancel()

        if self.tick_task:
            self.tick_task.cancel()

class RCFServer(object):
    address = None          # Server address
    port = None             # Server port
    snapshot = None         # Snapshot socket
    subscriber = None       # Incoming updates

    def __init__(self, ctx, address, port):
        self.address = address
        self.port = port
        self.snapshot = ctx.socket(zmq.DEALER)
        self.snapshot.linger = 0
        self.snapshot.connect("%s:%i".format(address.decode(),port))
        self.subscriber = ctx.socket(zmq.SUB)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, '')
        self.subscriber.connect("%s:%i".format(address.decode(),port+1))
        self.subscriber.linger = 0

class RCFClientAgent(object):
    ctx = None 
    pipe = None
    property_map = None
    publisher = None
    id = None
    state = State.INITIAL
    server = None

    def __init__(self, ctx, pipe, id):
        self.ctx = None 
        self.pipe = None
        self.property_map = None
        self.publisher = None
        self.id = None
        self.state = State.INITIAL
        self.server = None
        self.publisher = self.context.socket(zmq.PUSH) # push update socket
        self.publisher.setsockopt(zmq.IDENTITY, self.id)
        self.publisher.setsockopt(zmq.SNDHWM, 60)
        self.publisher.linger = 0
       

    def control_message (self):
        msg = self.pipe.recv_multipart()
        command = msg.pop(0)

        if command == b"CONNECT":
            address = msg.pop(0)
            port = int(msg.pop(0))

            if len(self.servers) < SERVER_MAX:
                self.server = RCFServer(self.ctx, address, port)
                self.publisher.connect("tcp://{}:5557".format(address.decode()))
                
            else:
                logger.error("E: too many servers (max. %i)", SERVER_MAX)


def rcf_client_agent(ctx,pipe,id):
    agent = RCFClientAgent(ctx,pipe,id)
    server = None

    while True:
        poller = zmq.Poller()
        poller.register(agent.pipe, zmq.POLLIN)
        server_socket = None

        if agent.state == State.INITIAL:
            server = agent.server
            if agent.servers:
                logger.info ("I: waiting for server at %s:%d...",
                    server.address, server.port)
                server.snapshot.send(b"SNAPSHOT_REQUEST")
                agent.state = State.SYNCING
        elif agent.state == State.SYNCING:
            sever_socket = server.snapshot
        elif agent.state == State.ACTIVE:
            server_socket = server.subscriber

        if server_socket:
            poller.register(server_socket, zmq.POLLIN)

        try:
            items = dict(poller.poll())
        except:
            raise
            break

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
                    action = "update" if kvmsg.body else "delete"
                    logging.info ("I: received from %s:%d %s",
                        server.address, server.port, action)
        else:
            agent.state = State.INITIAL



class RCFServerAgent():
    def __init__(self, context=zmq.Context(), id="admin"):
        self.context = context

        self.pub_sock = None
        self.request_sock = None
        self.collector_sock = None
        self.poller = None

        self.property_map = RCFStore()
        self.id = id
        self.bind_ports()
        # Main client loop registration
        tick()

        logger.info("{} client initialized".format(id))

    def bind_ports(self):
        # Update all clients
        self.pub_sock = self.context.socket(zmq.PUB)
        self.pub_sock.setsockopt(zmq.SNDHWM, 60)
        self.pub_sock.bind("tcp://*:5555")
        time.sleep(0.2)

        # Update request
        self.request_sock = self.context.socket(zmq.ROUTER)
        self.request_sock.setsockopt(zmq.IDENTITY, b'SERVER')
        self.request_sock.setsockopt(zmq.RCVHWM, 60)
        self.request_sock.bind("tcp://*:5556")

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
            socks = dict(self.poller.poll())

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
                msg = RCFMessage.recv(self.collector_sock)
                # Update all clients
                msg.store(self.property_map)
                msg.send(self.pub_sock)

    def stop(self):
        logger.debug("Stopping server")
        self.poller.unregister(self.request_sock)
        self.pub_sock.close()
        self.request_sock.close()
        self.collector_sock.close()

        self.status = RCFStatus.IDLE
