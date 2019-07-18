import logging
from uuid import uuid4
try:
    from .libs import umsgpack

except:
    # Server import
    from libs import umsgpack

import zmq
import pickle
from enum import Enum

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class RepState(Enum):
    ADDED = 0
    COMMITED = 1
    STAGED = 2


class ReplicatedDataFactory(object):
    """
    Manage the data types implementations 
    """

    def __init__(self):
        self.supported_types = []

        # Default registered types
        self.register_type(str,RepCommand)

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
    Datablock used for replication 
    """
    uuid = None     # uuid used as key      (string)
    pointer = None  # dcc data ref          (DCC type)
    buffer = None   # data blob             (json)
    str_type = None # data type name        (string)
    deps = [None]   # dependencies array    (string)
    owner = None    # Data owner            (string)
    state = None    # Data state            (RepState)

    def __init__(self, owner=None, data=None, uuid=None, buffer=None):
        self.uuid = uuid if uuid else str(uuid4())
        assert(owner)
        self.owner = owner
        self.pointer = data
        self.buffer = buffer if buffer else None
        self.str_type = type(self).__name__

    def push(self, socket):
        """
        Here send data over the wire:
            - serialize the data
            - send them as a multipart frame
        """
        data = self.serialize(self.pointer)
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
        data = self.deserialize(data)

        instance = factory.construct_from_net(str_type)(owner=owner, uuid=uuid, buffer=data)

        # instance.data = instance.deserialize(data)
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
        I want to load data from DCC

        DCC -> JSON

        MUST RETURN A BYTE ARRAY
        """
        raise NotImplementedError
    

    def apply(self,data,target):
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


    def dump(self):
        return self.deserialize(self.buffer)

class RepCommand(ReplicatedDatablock):
    
    def serialize(self,data):
        return pickle.dumps(data)

    def deserialize(self,data):
        return pickle.load(data)
    
    def apply(self,data,target):
        target = data

# class RepObject(ReplicatedDatablock):
#     def deserialize(self):
#         try:
#             if self.pointer is None:
#                 pointer = None

#                 # Object specific constructor...
#                 if self.data["data"] in bpy.data.meshes.keys():
#                     pointer = bpy.data.meshes[self.data["data"]]
#                 elif self.data["data"] in bpy.data.lights.keys():
#                     pointer = bpy.data.lights[self.data["data"]]
#                 elif self.data["data"] in bpy.data.cameras.keys():
#                     pointer = bpy.data.cameras[self.data["data"]]
#                 elif self.data["data"] in bpy.data.curves.keys():
#                     pointer = bpy.data.curves[self.data["data"]]
#                 elif self.data["data"] in bpy.data.armatures.keys():
#                     pointer = bpy.data.armatures[self.data["data"]]
#                 elif self.data["data"] in bpy.data.grease_pencils.keys():
#                     pointer = bpy.data.grease_pencils[self.data["data"]]
#                 elif self.data["data"] in bpy.data.curves.keys():
#                     pointer = bpy.data.curves[self.data["data"]]

#                 self.pointer = bpy.data.objects.new(self.data["name"], pointer)

#             self.pointer.matrix_world = mathutils.Matrix(self.data["matrix_world"])

#             self.pointer.id = self.data['id']

#             client = bpy.context.window_manager.session.username

#             if self.pointer.id == client or self.pointer.id == "Common":
#                 self.pointer.hide_select = False
#             else:
#                 self.pointer.hide_select = True

#         except Exception as e:
#             logger.error("Object {} loading error: {} ".format(self.data["name"], e))

#     def deserialize(self):
#         self.data = dump_datablock(self.pointer, 1)
