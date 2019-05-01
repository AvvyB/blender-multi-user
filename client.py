import binascii
import collections
import logging
import os
import sys
import threading
import time
from enum import Enum
from random import randint
import copy
import queue

import zmq
lock = threading.Lock()

try:
    from .libs import umsgpack
    # from .libs import zmq
    from .libs import dump_anything
    from . import helpers
    from . import message
except:
    # Server import
    from libs import umsgpack
    # from libs import zmq
    from libs import dump_anything
    import helpers
    import message

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
        self.queue = queue.Queue()
        self.agent = threading.Thread(
            target=rcf_client_agent, args=(self.ctx, peer, self.queue), name="net-agent")
        self.agent.daemon = True
        self.agent.start()
        # self.sync_agent = threading.Thread(
        #     target=rcf_sync_agent, args=(self.ctx, self.pipe), name="sync-agent")
        # self.sync_agent.daemon = True
        # self.sync_agent.start()

    def connect(self, id, address, port):
        self.pipe.send_multipart([b"CONNECT", (id.encode() if isinstance(
            id, str) else id), (address.encode() if isinstance(
                address, str) else address), b'%d' % port])
    def init(self):
        """Set new value in distributed hash table
        Sends [SET][key][value] to the agent
        """
        self.pipe.send_multipart(
            [b"INIT"])

    def disconnect(self):
        """
        Disconnect
        """
        self.pipe.send_multipart(
            [b"DISCONNECT"]) 

    def set(self, key, value=None, override=False):
        """Set new value in distributed hash table
        Sends [SET][key][value] to the agent
        """
        self.pipe.send_multipart(
            [b"SET", umsgpack.packb(key), (umsgpack.packb(value) if value else umsgpack.packb('None')),umsgpack.packb(override)])

    def add(self, key, value=None):
        """Set new value in distributed hash table
        Sends [SET][key][value] to the agent
        """
        self.pipe.send_multipart(
            [b"ADD", umsgpack.packb(key), (umsgpack.packb(value) if value else umsgpack.packb('None'))])

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
            self.disconnect()

            # Disconnect time
            time.sleep(0.2)

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

    def state(self):
        self.pipe.send_multipart([b"STATE"])
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
        self.snapshot.setsockopt(zmq.IDENTITY, id)
        self.snapshot.connect("tcp://{}:{}".format(address.decode(), port))
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
    serial = None
    serialisation_agent = None

    def __init__(self, ctx, pipe):
        self.ctx = ctx
        self.pipe = pipe
        self.property_map = {}
        self.id = b"test"
        self.state = State.INITIAL
        self.admin = False
        self.server = None
        self.publisher = self.ctx.socket(zmq.PUSH)  # push update socket
        self.publisher.setsockopt(zmq.IDENTITY, self.id)
        self.publisher.setsockopt(zmq.SNDHWM, 60)
        self.publisher.linger = 0
        self.serial, peer = zpipe(self.ctx)
        self.updates = queue.Queue()
        # self.serial_agent = threading.Thread(
        #     target=serialization_agent, args=(self.ctx, peer), name="serial-agent")
        # self.serial_agent.daemon = True
        # self.serial_agent.start()
    def _add(self,key, value='None'):
        if value == 'None':
            # try to dump from bpy
            # logging.info(key)
            value = helpers.dump(key)
            value['id'] = self.id.decode()
        if value:
            rcfmsg = message.RCFMessage(
                key=key, id=self.id, body=value)

            rcfmsg.store(self.property_map)
            rcfmsg.send(self.publisher)
        else:
            logger.error("Fail to dump ")

    def control_message(self):
        msg = self.pipe.recv_multipart()
        command = msg.pop(0)

        if command == b"CONNECT":
            self.id = msg.pop(0)
            address = msg.pop(0)
            port = int(msg.pop(0))

            if self.server is None:
                if address == '127.0.0.1' or address == 'localhost' :
                    self.admin = True
                self.server = RCFServer(self.ctx, address, port, self.id)
                self.publisher.connect(
                    "tcp://{}:{}".format(address.decode(), port+2))

            else:
                logger.error("E: too many servers (max. %i)", SERVER_MAX)

        elif command == b"DISCONNECT":
            if self.admin is False:
                uid = self.id.decode()
                
                delete_user = message.RCFMessage(
                                key="Client/{}".format(uid), id=self.id, body=None)
                delete_user.send(self.publisher)

                # TODO: Do we need to pass every object rights to the moderator ?
                # for k,v in self.property_map.items():
                #     if v.body["id"] == uid:
                #         delete_msg = message.RCFMessage(
                #                 key=k, id=self.id, body=None)
                #         # delete_msg.store(self.property_map)
                #         delete_msg.send(self.publisher)
                        
        elif command == b"SET":
            key = umsgpack.unpackb(msg[0])
            value = umsgpack.unpackb(msg[1])
            override = umsgpack.unpackb(msg[2])

            if key in self.property_map.keys():
                if self.property_map[key].body['id'] == self.id.decode() or override:
                    if value == 'None':
                        value = helpers.dump(key)
                        value['id'] = self.id.decode()
                    if value:
                        key_id = self.id

                        # if override:
                        #     key_id = value['id'].encode()

                        rcfmsg = message.RCFMessage(
                            key=key, id=key_id, body=value)

                        rcfmsg.store(self.property_map)
                        
                        if override:
                            helpers.load(key,self.property_map[key].body)
                        rcfmsg.send(self.publisher)
                    else:
                        logger.error("Fail to dump ")
                else:
                    helpers.load(key,self.property_map[key].body)
        
        elif command == b"INIT":
            d = helpers.get_all_datablocks()
            for i in d:
                self._add(i)

        elif command == b"ADD":
            key = umsgpack.unpackb(msg[0])
            value = umsgpack.unpackb(msg[1])

            if value == 'None':
                # try to dump from bpy
                # logging.info(key)
                value = helpers.dump(key)
                value['id'] = self.id.decode()
            if value:
                rcfmsg = message.RCFMessage(
                    key=key, id=self.id, body=value)

                rcfmsg.store(self.property_map)
                rcfmsg.send(self.publisher)
            else:
                logger.error("Fail to dump ")

        elif command == b"GET":
            value = []
            key = umsgpack.unpackb(msg[0])
            for k in self.property_map.keys():
                if key in k:
                    value.append([k, self.property_map.get(k).body])

            # value = [self.property_map.get(key) for key in keys]
            # value = self.property_map.get(key)
            self.pipe.send(umsgpack.packb(value)
                           if value else umsgpack.packb(''))

        elif command == b"LIST":
            dump_list = []
            for k,v in self.property_map.items():
                if 'Client' in k:
                    dump_list.append([k,v.id.decode()])
                else:
                    try:
                        dump_list.append([k,v.body['id']])
                    except:
                        pass
            self.pipe.send(umsgpack.packb(dump_list)
                           if dump_list else umsgpack.packb(''))

        elif command == b"STATE":
            self.pipe.send(umsgpack.packb(self.state.value))

def rcf_client_agent(ctx, pipe, queue):
    agent = RCFClientAgent(ctx, pipe)
    server = None
    update_queue = queue
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
                            agent.id.decode(), server.address, server.port)
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
                    client_key = "Client/{}".format(agent.id.decode())
                    client_dict = {}

                    with lock:
                        client_dict = helpers.init_client(key=client_key)
                        client_dict['id'] = agent.id.decode()
                    client_store = message.RCFMessage(
                        key=client_key, id=agent.id, body=client_dict)
                    logger.info(client_store)
                    client_store.store(agent.property_map)
                    client_store.send(agent.publisher)
                    logger.info("snapshot complete")
                    agent.state = State.ACTIVE
                else:
                    helpers.load(rcfmsg.key, rcfmsg.body)
                    
                    rcfmsg.store(agent.property_map)
                    logger.info("snapshot from {} stored".format(rcfmsg.id))
            elif agent.state == State.ACTIVE:
                # IN
                if rcfmsg.id != agent.id:
                    # update_queue.put((rcfmsg.key,rcfmsg.body))
                   
                    # try:
                    #     logger.info(rcfmsg.body['id'])
                    # except:
                    #     pass
                    
                    with lock:
                        helpers.load(rcfmsg.key, rcfmsg.body)
                    rcfmsg.store(agent.property_map)
                    # elif rcfmsg.id == agent.property_map[rcfmsg.key].id:
                    #     with lock:
                    #         helpers.load(rcfmsg.key, rcfmsg.body)
                        # logger.info("load")
                        # agent.serial.send_multipart([b"LOAD", umsgpack.packb(rcfmsg.key), umsgpack.packb(rcfmsg.body)])

                        # reply = agent.serial.recv_multipart()

                        # if reply == b"DONE":
                        # rcfmsg.store(agent.property_map)
                        # action = "update" if rcfmsg.body else "delete"
                        # logging.info("{}: received from {}:{},{} {}".format(rcfmsg.key,
                        #     server.address, rcfmsg.id, server.port, action))
                else:
                    logger.debug("{} nothing to do".format(agent.id))

                # LOCAL SYNC
                # if not update_queue.empty():
                #     key = update_queue.get()

                #     value = helpers.dump(key)
                #     value['id'] = agent.id.decode()
                #     if value:
                #         rcfmsg = message.RCFMessage(
                #             key=key, id=agent.id, body=value)

                #         rcfmsg.store(agent.property_map)
                #         rcfmsg.send(agent.publisher)
                #     else:
                #         logger.error("Fail to dump ")




    logger.info("exit thread")
    stop = False
    # else: else
    #     agent.state = State.INITIAL


class SerializationAgent(object):
    ctx = None
    pipe = None

    def __init__(self, ctx, pipe):
        self.ctx = ctx
        self.pipe = pipe
        logger.info("serialisation service launched")

    def control_message(self):
        msg = self.pipe.recv_multipart()
        command = msg.pop(0)

        if command == b"DUMP":
            key = umsgpack.unpackb(msg[0])

            value = helpers.dump(key)

            self.pipe.send_multipart(umsgpack.packb(value))

        elif command == b"LOAD":

            key = umsgpack.unpackb(msg[0])
            value = umsgpack.unpackb(msg[1])

            helpers.load(key, value)

            self.pipe.send_multipart([b"DONE"])


def serialization_agent(ctx, pipe):
    agent = SerializationAgent(ctx, pipe)

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


class RCFSyncAgent(object):
    ctx = None
    pipe = None

    def __init__(self, feed):
        self.feed = feed
        logger.info("sync service launched")
    



def rcf_sync_agent(ctx, feed):
    agent = RCFSyncAgent(feed)

    global stop
    while True:
        if stop:
            break

        # Synchronisation

