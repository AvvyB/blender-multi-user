import logging
from .libs.dump_anything import dump_datablock
from uuid import uuid4
try:
    from .libs import umsgpack

except:
    # Server import
    from libs import umsgpack

import zmq

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class ReplicatedDatablock(object):
    """
    Datablock used for replication 
    """
    uuid = None  # key (string)
    data = None  # data blob
    pointer = None # dcc data reference

    def __init__(self, owner=None,  data=None):
        self.uuid = str(uuid4())
        assert(owner)
        self.pointer = data
        

    def push(self, socket):
        """
        Here send data over the wire
        """
        pass
   
    @classmethod
    def pull(cls, socket):
        """
        Here we reeceive data from the wire
        """
        uuid, owner,  body = socket.recv_multipart(zmq.NOBLOCK)
        key = key.decode() if key else None
        id = id if id else None
        body = umsgpack.unpackb(body) if body else None

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

    def decode_data(self):
        """
        I want to apply changes into the DCC
        """
        raise NotImplementedError
   
    
    def encode_data(self):
        """
        I want to load data from DCC
        """
        raise NotImplementedError

class RpTest(ReplicatedDatablock):
    def decode_data(self):
        test_data = {}


# class RpObject(ReplicatedDatablock):
#     def decode_data(self):
#         try:
#             if self.pointer is None:
#                 pointer = None
                
#                 # Object specific constructor...
#                 if data["data"] in bpy.data.meshes.keys():
#                     pointer = bpy.data.meshes[data["data"]]
#                 elif data["data"] in bpy.data.lights.keys():
#                     pointer = bpy.data.lights[data["data"]]
#                 elif data["data"] in bpy.data.cameras.keys():
#                     pointer = bpy.data.cameras[data["data"]]
#                 elif data["data"] in bpy.data.curves.keys():
#                     pointer = bpy.data.curves[data["data"]]
#                 elif data["data"] in bpy.data.armatures.keys():
#                     pointer = bpy.data.armatures[data["data"]]
#                 elif data["data"] in bpy.data.grease_pencils.keys():
#                     pointer = bpy.data.grease_pencils[data["data"]]
#                 elif data["data"] in bpy.data.curves.keys():
#                     pointer = bpy.data.curves[data["data"]]

#                 self.pointer = bpy.data.objects.new(data["name"], pointer)

#             self.pointer.matrix_world = mathutils.Matrix(data["matrix_world"])

#             self.pointer.id = data['id']

#             client = bpy.context.window_manager.session.username

#             if self.pointer.id == client or self.pointer.id == "Common":
#                 self.pointer.hide_select = False
#             else:
#                 self.pointer.hide_select = True
        
#         except Exception as e:
#             logger.error("Object {} loading error: {} ".format(data["name"], e))

#     def encode_data(self):
#         self.data = dump_datablock(self.pointer, 1)


o = BpyObject("toto")