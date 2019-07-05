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
        types.append((supported_types, implementation))

    def match_type(self,data):
        for stypes, implementation in self.supported_types: 
            if isinstance(data, stypes):
                return implementation
        
        print("type not supported for replication")
        raise NotImplementedError

    def construct(self,data):
        implementation = self.match_type(data)
        return implementation

class ReplicatedDatablock(object):
    """
    Datablock used for replication 
    """
    uuid = None  # key (string)
    pointer = None # dcc data reference
    data = None  # data blob (json)
    deps = None # dependencies references

    def __init__(self, owner=None, data=None):
        self.uuid = str(uuid4())
        assert(owner)
        self.pointer = data
        

    def push(self, socket):
        """
        Here send data over the wire:
            - serialize the data
            - send them as a multipart frame
        """
        data = self.serialize(self.pointer)
        assert(isinstance(data, bytes))

        key = self.uuid.encode()
        
        socket.send_multipart([])
   
    @classmethod
    def pull(cls, socket):
        """
        Here we reeceive data from the wire:
            - read data from the socket
            - reconstruct an instance
        """
        pass

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
        pass

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


