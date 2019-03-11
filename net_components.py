import zmq
import asyncio
import logging
from .libs import umsgpack
import time
import random
import struct
import collections

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RCFFactory(object):
    """
    Abstract layer used to bridge external and inter
    """
    def init(self, data):
        """
        set the RCFMessage pointer to local data
        """
        print("Default setter")
        #Setup data accessor
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

    def apply(self,data):
        pass

    def diff(self, data):
        """
        Verify data integrity 
        """
        pass

class RCFStore(collections.MutableMapping,dict):
    def __init__(self, custom_factory=RCFFactory()):
        super().__init__() 
        self.factory = custom_factory
        print("name {}".format(custom_factory.__class__.__name__))
        
    def __getitem__(self,key):
        # if self[key]:
            # Get dict data from external
            # print("getting item from store")
        return dict.__getitem__(self,key)

    def __setitem__(self, key, value):
        #test
        # TODO: test with try - except KeyError
        # if key in self:
        #     # Set dict data from external
        #     dict.__setitem__(self,key,value)
        # else:
        #     print("{}".format(value))
        #     self.factory.init(value)

        dict.__setitem__(self,key,value)
           
    def __delitem__(self, key):
        dict.__delitem__(self,key)
    def __iter__(self):
        return dict.__iter__(self)
    def __len__(self):
        return dict.__len__(self)
    def __contains__(self, x):
        return dict.__contains__(self,x)

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

    def __init__(self, key=None, id=None, mtype=None, body=None, pointer=None):
        self.key = key
        self.mtype = mtype
        self.body = body
        self.id = id
        self.pointer = pointer
        self.get = None
        self.set = None
    def store(self, dikt):
        """Store me in a dict if I have anything to store"""
        # this currently erasing old value
        if self.key is not None and self.body is not None:
            dikt[self.key] = self

    def send(self, socket):
        """Send key-value message to socket; any empty frames are sent as such."""
        key = ''.encode() if self.key is None else self.key.encode()
        mtype = ''.encode() if self.mtype is None else self.mtype.encode()
        body = ''.encode() if self.body is None else umsgpack.packb(self.body)
        id = ''.encode() if self.id is None else self.id

        try:
            socket.send_multipart([key, id, mtype, body])
        except:
            logger.info("Fail to send {}".format(key))

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

class Client():
    def __init__(
        self, 
        context=zmq.Context(), 
        id="default", 
        on_recv=None, 
        on_post_init=None, 
        is_admin=False, 
        factory=None):

        self.is_admin = is_admin

        # 0MQ vars
        self.context = context
        self.pull_sock = None
        self.req_sock = None
        self.poller = None

        self.id = id.encode()
        self.on_recv = on_recv
        self.on_post_init = on_post_init
        self.bind_ports()

        # Main client loop registration
        self.task = asyncio.ensure_future(self.main())

        self.property_map = RCFStore(custom_factory=factory)

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
        # self.req_sock.setsockopt(zmq.SNDHWM, 60)
        self.req_sock.linger = 0
        self.req_sock.connect("tcp://localhost:5556")

        # push update socket
        self.push_sock = self.context.socket(zmq.PUSH)
        self.push_sock.setsockopt(zmq.IDENTITY, self.id)
        self.push_sock.linger = 0
        self.push_sock.connect("tcp://localhost:5557")
        self.push_sock.setsockopt(zmq.SNDHWM, 60)

        # Sockets aggregator, not really used for now
        self.poller = zmq.Poller()
        self.poller.register(self.pull_sock, zmq.POLLIN)

        time.sleep(0.1)

    async def main(self):
        logger.info("{} client syncing".format(id))

        # Late join mecanism
        logger.info("{} send snapshot request".format(id))
        self.req_sock.send(b"SNAPSHOT_REQUEST")
        while True:
            try:
                rcfmsg_snapshot = RCFMessage.recv(self.req_sock)

                if rcfmsg_snapshot.key == "SNAPSHOT_END":
                    logger.info("snapshot complete")
                    break
                else:
                    logger.info("received : {}".format(rcfmsg_snapshot.key))
                    rcfmsg_snapshot.store(self.property_map)
            except:
                await asyncio.sleep(0.001)

        for f in self.on_post_init:
            f()

        logger.info("{} client running".format(id))

        # Main loop
        while True:
            # TODO: find a better way
            socks = dict(self.poller.poll(1))

            if self.pull_sock in socks:
                rcfmsg = RCFMessage.recv(self.pull_sock)
                
                # if rcfmsg.pointer:
                rcfmsg.store(self.property_map)


                for f in self.on_recv:
                    f(rcfmsg)
            else:
                await asyncio.sleep(0.001)

    def push_update(self, key, mtype, body):
        rcfmsg = RCFMessage(key, self.id, mtype, body)
        rcfmsg.send(self.push_sock)
        # self.push_sock.send_multipart()

    def stop(self):
        logger.debug("Stopping client")
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

        self.property_map =  RCFStore()
        self.id = id
        self.bind_ports()
        # Main client loop registration
        self.task = asyncio.ensure_future(self.main())

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

    async def main(self):
        logger.info("{} server launched".format(id))

        while True:
            # Non blocking poller 
            socks = dict(self.poller.poll(1))

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
            else:
                await asyncio.sleep(0.001)

    def stop(self):
        logger.debug("Stopping server")
        self.poller.unregister(self.request_sock)
        self.pub_sock.close()
        self.request_sock.close()
        self.collector_sock.close()
        self.task.cancel()
