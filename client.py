import binascii
import collections
import copy
import logging
import os
import queue
import sys
import threading
import time
from enum import Enum
from random import randint
import zmq
import json

from . import environment,replication, helpers, message
from .libs import dump_anything, umsgpack

CONNECT_TIMEOUT = 2
WATCH_FREQUENCY = 0.1
WAITING_TIME = 0.001
SERVER_MAX = 1
DUMP_AGENTS_NUMBER = 1

lock = threading.Lock()
logger = logging.getLogger(__name__)
logging.basicConfig(level=environment)
instance = None 


class State(Enum):
    INITIAL = 1
    SYNCING = 2
    ACTIVE = 3
    WORKING = 4


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


class Client(object):
    ctx = None
    pipe = None
    net_agent = None
    store = None
    active_tasks = None

    def __init__(self, executor):
        self.ctx = zmq.Context()
        self.pipe, peer = zpipe(self.ctx)
        self.store = {}
        self.serial_product = queue.Queue()
        self.serial_feed = queue.Queue()
        self.stop_event = threading.Event()
        self.external_tasks = executor

        # Net agent
        self.net_agent = threading.Thread(
            target=net_worker,
            args=(self.ctx, self.store, peer, self.serial_product, self.serial_feed, self.stop_event,self.external_tasks), name="net-agent")
        self.net_agent.daemon = True
        self.net_agent.start()

        # Local data translation agent
        self.serial_agents = []
        for a in range(0, DUMP_AGENTS_NUMBER):
            serial_agent = threading.Thread(
                target=serial_worker, args=(self.serial_product, self.serial_feed), name="serial-agent")
            serial_agent.daemon = True
            serial_agent.start()
            self.serial_agents.append(serial_agent)

        # Sync agent
        self.watchdog_agent = threading.Thread(
            target=watchdog_worker, args=(self.serial_feed,WATCH_FREQUENCY, self.stop_event), name="watchdog-agent")
        self.watchdog_agent.daemon = True
        self.watchdog_agent.start()

        # Status
        self.active_tasks = 0

    def connect(self, id, address, port):
        self.pipe.send_multipart([b"CONNECT", (id.encode() if isinstance(
            id, str) else id), (address.encode() if isinstance(
                address, str) else address), b'%d' % port])

    def replicate(self, py_object):
        """Entry point for python object replication
            - Create object replication structure
            - Add it to the distributed hash table
        """
        pass
        # node = Factory(py_object)

        # self.store
    def init(self):
        """
        Scene initialisation
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

        if value:
            key = umsgpack.packb(key)
            value = umsgpack.packb(value) if value else umsgpack.packb('None')
            override = umsgpack.packb(override)

            self.pipe.send_multipart(
                [b"SET", key, value, override])
        else:
            self.serial_feed.put(('DUMP', key, None))

    def add(self, key, value=None):
        """Set new value in distributed hash table
        """
        self.serial_feed.put(key)

    def is_busy(self):
        self.active_tasks = self.serial_feed.qsize() + self.serial_product.qsize()
        if self.active_tasks == 0:
            return False
        else:
            return True

    def exit(self):
        if self.net_agent.is_alive():
            self.disconnect()

        self.stop_event.set()

        for a in range(0, DUMP_AGENTS_NUMBER):
            self.serial_feed.put(('STOP', None, None))

    # READ-ONLY FUNCTIONS
    def get(self, key):
        """Lookup value in distributed hash table
        Sends [GET][key] to the agent and waits for a value response
        If there is no clone available, will eventually return None.
        """
        value = []

        for k in self.store.keys():
            if key in k:
                value.append([k, self.store.get(k).body])

        return value

    def exist(self, key):
        """
        Fast key exist check
        """

        if key in self.store.keys():
            return True
        else:
            return False

    def list(self):
        dump_list = []
        for k, v in self.store.items():
            if 'Client' in k:
                dump_list.append([k, v.id.decode()])
            else:
                try:
                    dump_list.append([k, v.body['id']])
                except:
                    pass

        return dump_list

    def state(self):
        if self.net_agent is None or not self.net_agent.is_alive():
            return 1 #State.INITIAL
        elif self.net_agent.is_alive() and self.store.keys():
            return 3 # State.ACTIVE
        else:
            return 2 #State.SYNCING
        

    # SAVING FUNCTIONS
    def dump(self, filepath):
        with open('dump.json', "w") as fp:
            for key, value in self.store.items():
                line = json.dumps(value.body)
                fp.write(line)


class Server(object):
    address = None          # Server address
    port = None             # Server port
    snapshot = None         # Snapshot socket
    subscriber = None       # Incoming updates

    def __init__(self, ctx, address, port, id):
        self.address = address
        self.port = port
        self.snapshot = ctx.socket(zmq.DEALER)
        self.snapshot = self.context.socket(zmq.DEALER)
        self.snapshot.setsockopt(zmq.IDENTITY, id)
        self.snapshot.connect("tcp://{}:{}".format(address.decode(), port))
        self.subscriber = ctx.socket(zmq.SUB)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, '')
        self.subscriber.connect("tcp://{}:{}".format(address.decode(), port+1))
        self.subscriber.linger = 0
        print("connected on tcp://{}:{}".format(address.decode(), port))


class ClientAgent(object):
    ctx = None
    pipe = None
    property_map = None
    publisher = None
    id = None
    state = None
    server = None
    serial = None
    serialisation_agent = None

    def __init__(self, ctx, store, pipe):
        self.ctx = ctx
        self.pipe = pipe
        self.property_map = store
        self.id = b"test"
        self.state = State.INITIAL
        self.admin = False
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
                if address == '127.0.0.1' or address == 'localhost':
                    self.admin = True
                self.server = Server(self.ctx, address, port, self.id)
                self.publisher.connect(
                    "tcp://{}:{}".format(address.decode(), port+2))

            else:
                logger.error("E: too many servers (max. %i)", SERVER_MAX)

        elif command == b"DISCONNECT":
            if self.admin is False:
                uid = self.id.decode()

                delete_user = message.Message(
                    key="Client/{}".format(uid), id=self.id, body=None)
                delete_user.send(self.publisher)

                # TODO: Do we need to pass every object rights to the moderator on disconnect?
                # for k,v in self.property_map.items():
                #     if v.body["id"] == uid:
                #         delete_msg = message.Message(
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
                        msg = message.Message(
                            key=key, id=key_id, body=value)

                        msg.store(self.property_map)

                        if override:
                            helpers.load(key, self.property_map[key].body)
                        msg.send(self.publisher)
                    else:
                        logger.error("Fail to dump ")
                else:
                    helpers.load(key, self.property_map[key].body)

        elif command == b"ADD":
            key = umsgpack.unpackb(msg[0])
            value = umsgpack.unpackb(msg[1])

            if value == 'None':
                value = helpers.dump(key)
                value['id'] = self.id.decode()
            if value:
                msg = message.Message(
                    key=key, id=self.id, body=value)

                msg.store(self.property_map)
                msg.send(self.publisher)
            else:
                logger.error("Fail to dump ")

        elif command == b"GET":
            value = []
            key = umsgpack.unpackb(msg[0])
            for k in self.property_map.keys():
                if key in k:
                    value.append([k, self.property_map.get(k).body])

            self.pipe.send(umsgpack.packb(value)
                           if value else umsgpack.packb(''))

        elif command == b"LIST":
            dump_list = []
            for k, v in self.property_map.items():
                if 'Client' in k:
                    dump_list.append([k, v.id.decode()])
                else:
                    try:
                        dump_list.append([k, v.body['id']])
                    except:
                        pass
            self.pipe.send(umsgpack.packb(dump_list)
                           if dump_list else umsgpack.packb(''))

        elif command == b"STATE":
            self.pipe.send(umsgpack.packb(self.state.value))


def net_worker(ctx, store, pipe, serial_product, serial_feed, stop_event,external_executor):
    agent = ClientAgent(ctx, store, pipe)
    server = None
    net_feed = serial_product
    net_product = serial_feed
    external_executor = external_executor
    while not stop_event.is_set():
        poller = zmq.Poller()
        poller.register(agent.pipe, zmq.POLLIN)
        server_socket = None

        if agent.state == State.INITIAL:
            server = agent.server
            if agent.server:
                logger.debug("%s: waiting for server at %s:%d...",
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
            msg = message.Message.recv(server_socket)

            if agent.state == State.SYNCING:
                # CLient snapshot
                if msg.key == "SNAPSHOT_END":
                    client_key = "Client/{}".format(agent.id.decode())

                    client_dict = {}
                    client_dict = helpers.init_client(key=client_key)
                    client_dict['id'] = agent.id.decode()

                    client_store = message.Message(
                        key=client_key, id=agent.id, body=client_dict)
                    client_store.store(agent.property_map)
                    client_store.send(agent.publisher)

                    agent.state = State.ACTIVE
                    logger.debug("snapshot complete")
                else:
                    net_product.put(('LOAD', msg.key, msg.body))
                    
                    # helpers.load(msg.key, msg.body)
                    msg.store(agent.property_map)
                    logger.debug("snapshot from {} stored".format(msg.id))
            elif agent.state == State.ACTIVE:
                if msg.id != agent.id:

                    # with lock:
                    #     helpers.load(msg.key, msg.body)
                    msg.store(agent.property_map)
                    # net_product.put(('LOAD', msg.key, msg.body))
                    params = []
                    params.append(msg.key)
                    params.append(msg.body)
                    external_executor.put((helpers.load,params))
                else:
                    logger.debug("{} nothing to do".format(agent.id))

        # Serialisation thread  => Net thread
        if not net_feed.empty():
            key, value = net_feed.get()
            if value:
                # Stamp with id
                value['id'] = agent.id.decode()

                # Format massage
                msg = message.Message(
                    key=key, id=agent.id, body=value)

                msg.store(agent.property_map)
                msg.send(agent.publisher)
            else:
                logger.error("Fail to dump ")

    logger.info("exit thread")


def serial_worker(serial_product,  serial_feed):
    logger.info("serial thread launched")

    while True:
        command, key, value = serial_feed.get()

        if command == 'STOP':
            break
        elif command == 'DUMP':
            try:
                value = helpers.dump(key)

                if value:
                    serial_product.put((key, value))
            except Exception as e:
                logger.error("{}".format(e))
        elif command == 'LOAD':
            if value:
                try:
                    helpers.load(key, value)
                except Exception as e:
                    logger.error("{}".format(e))

    logger.info("serial thread stopped")


def watchdog_worker(serial_feed, interval, stop_event):
    import bpy

    logger.info(
        "watchdog thread launched with {} sec of interval".format(interval))
    while not stop_event.is_set():
        for datatype in environment.rtypes:
            for item in getattr(bpy.data,  helpers.BPY_TYPES[datatype]):
                key = "{}/{}".format(datatype, item.name)
                try:
                    if item.is_dirty:
                        logger.debug("{} needs update".format(key))
                        serial_feed.put(('DUMP', key, None))
                        item.is_dirty = False
                except:
                    pass
        time.sleep(interval)

    logger.info("watchdog thread stopped")


