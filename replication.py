import logging
from uuid import uuid4
try:
    from .libs import umsgpack

except:
    # Server import
    from libs import umsgpack

import zmq

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
class ReplicatedDataFactory(object):
    """
    Manage the data types implamentations 
    """
    def __init__(self):
        self.supported_types = []
    
    def register_type(self,dtype, implementation):
        """
        Register a new replicated datatype implementation 
        """
        self.supported_types.append((dtype, implementation))

    def match_type_by_instance(self,data):
        """
        Find corresponding type to the given datablock
        """
        for stypes, implementation in self.supported_types: 
            if isinstance(data, stypes):
                return implementation
    
        print("type not supported for replication")
        raise NotImplementedError

    def construct_from_dcc(self,data):
        implementation = self.match_type_by_instance(data)
        return implementation

    def construct_from_net(self, type_name):
        """
        Reconstruct a new replicated value from serialized data
        """
        return self.match_type_by_name(data)

class ReplicatedDatablock(object):
    """
    Datablock used for replication 
    """
    uuid = None  # key (string)
    pointer = None # dcc data reference
    data = None  # data blob (json)
    str_type = None # data type name (for deserialization)
    deps = None # dependencies references
    owner = None

    def __init__(self, owner=None, data=None, uuid=None):
        self.uuid = uuid if uuid else str(uuid4())
        assert(owner)
        self.owner = owner
        self.pointer = data

        if data:
            self.str_type = self.data.__class__.__name__
        

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
        
        socket.send_multipart([key,owner,data])
   
    @classmethod
    def pull(cls, socket, factory):
        """
        Here we reeceive data from the wire:
            - read data from the socket
            - reconstruct an instance
        """
        uuid, owner, data = socket.recv_multipart(zmq.NOBLOCK)

        instance = factory.construct_from_net(data)(owner=owner.decode(), uuid=uuid.decode())

        instance.data = instance.deserialize(data)
        return instance


    def store(self, dict, persistent=False): 
        """
        I want to store my replicated data. Persistent means into the disk
        If uuid is none we delete the key from the volume
        """
        if self.uuid is not None:
            if self.data == 'None':
                logger.info("erasing key {}".format(self.uuid))
                del dict[self.uuid]
            else:
                dict[self.uuid] = self
                
            return self.uuid

    def deserialize(self,data):
        """
        I want to apply changes into the DCC

        MUST RETURN AN OBJECT INSTANCE
        """
        raise NotImplementedError
   
    
    def serialize(self,data):
        """
        I want to load data from DCC

        MUST RETURN A BYTE ARRAY
        """
        raise NotImplementedError




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


