import json
import logging
import pickle
from enum import Enum
from uuid import uuid4

import zmq

logger = logging.getLogger(__name__)


class RepState(Enum):
    ADDED = 0
    COMMITED = 1
    STAGED = 2


class ReplicatedDataFactory(object):
    """
    Manage the data types implementations.

    """

    def __init__(self):
        self.supported_types = []

        # Default registered types
        self.register_type(str, RepCommand)
        self.register_type(RepDeleteCommand, RepDeleteCommand)

    def register_type(self, dtype, implementation):
        """
        Register a new replicated datatype implementation 
        """
        self.supported_types.append((dtype, implementation))

    def match_type_by_instance(self, data):
        """
        Find corresponding type to the given datablock
        """
        for stypes, implementation in self.supported_types:
            if isinstance(data, stypes):
                return implementation

        print("type not supported for replication")
        raise NotImplementedError

    def match_type_by_name(self, type_name):
        for stypes, implementation in self.supported_types:
            if type_name == implementation.__name__:
                return implementation
        print("type not supported for replication")
        raise NotImplementedError

    def construct_from_dcc(self, data):
        implementation = self.match_type_by_instance(data)
        return implementation

    def construct_from_net(self, type_name):
        """
        Reconstruct a new replicated value from serialized data
        """
        return self.match_type_by_name(type_name)


class ReplicatedDatablock(object):
    """
    Datablock definition that handle object replication logic.
    PUSH: send the object over the wire
    STORE: register the object on the given replication graph
    LOAD: apply loaded changes by reference on the local copy
    DUMP: get local changes

    """
    uuid = None     # uuid used as key      (string)
    pointer = None  # dcc data ref          (DCC type)
    buffer = None   # raw data              (json)
    str_type = None  # data type name        (string)
    deps = [None]   # dependencies array    (string)
    owner = None    # Data owner            (string)
    state = None    # Data state            (RepState)

    def __init__(self, owner=None, pointer=None, uuid=None, buffer=None):
        self.uuid = uuid if uuid else str(uuid4())
        assert(owner)
        self.owner = owner

        if pointer:
            self.pointer = pointer
            self.buffer = self.dump()
        elif buffer:
            self.buffer = buffer

        self.str_type = type(self).__name__

    def push(self, socket):
        """
        Here send data over the wire:
            - serialize the data
            - send them as a multipart frame thought the given socket
        """
        assert(self.buffer)

        data = self.serialize(self.buffer)
        assert(isinstance(data, bytes))
        owner = self.owner.encode()
        key = self.uuid.encode()
        type = self.str_type.encode()

        socket.send_multipart([key, owner, type, data])

    @classmethod
    def pull(cls, socket, factory):
        """
        Here we reeceive data from the wire:
            - read data from the socket
            - reconstruct an instance
        """
        uuid, owner, str_type, data = socket.recv_multipart(zmq.NOBLOCK)

        str_type = str_type.decode()
        owner = owner.decode()
        uuid = uuid.decode()

        instance = factory.construct_from_net(str_type)(owner=owner, uuid=uuid)
        instance.buffer = instance.deserialize(data)

        return instance

    def store(self, dict, persistent=False):
        """
        I want to store my replicated data. Persistent means into the disk
        If uuid is none we delete the key from the volume
        """
        if self.uuid is not None:
            if self.buffer == 'None':
                logger.debug("erasing key {}".format(self.uuid))
                del dict[self.uuid]
            else:
                dict[self.uuid] = self

            return self.uuid

    def deserialize(self, data):
        """
        BUFFER -> JSON
        """
        raise NotImplementedError

    def serialize(self, data):
        """
        JSON -> BUFFER
        """
        raise NotImplementedError

    def dump(self):
        """
        DCC -> JSON
        """
        assert(self.pointer)

        return json.dumps(self.pointer)

    def load(self, target=None):
        """
        JSON -> DCC
        """
        raise NotImplementedError

    def resolve(self):
        """
        I want to resolve my orphan data to an existing one 
        = Assing my pointer

        """
        raise NotImplementedError

    def __repr__(self):
        return "{uuid} - owner: {owner} - type: {type}".format(
            uuid=self.uuid,
            owner=self.owner,
            type=self.str_type
        )


class RepCommand(ReplicatedDatablock):
    def serialize(self, data):
        return pickle.dumps(data)

    def deserialize(self, data):
        return pickle.loads(data)

    def load(self, target):
        target = self.pointer


class RepDeleteCommand(ReplicatedDatablock):
    def serialize(self, data):
        return pickle.dumps(data)

    def deserialize(self, data):
        return pickle.loads(data)

    def store(self, rep_store):
        assert(self.buffer)

        if rep_store and self.buffer in rep_store.keys():
            del rep_store[self.buffer]
