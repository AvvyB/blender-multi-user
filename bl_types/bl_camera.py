import bpy
import mathutils
from jsondiff import diff

from .. import utils
from .bl_datablock import BlDatablock

class BlCamera(BlDatablock):
    def __init__(self, *args, **kwargs):
        self.icon = 'CAMERA_DATA'

        super().__init__( *args, **kwargs)
        
        
    def load(self, data, target):
        utils.dump_anything.load(target, data)

    def construct(self, data):
        return bpy.data.cameras.new(data["name"])

    def dump(self, pointer=None):
        assert(pointer)
        
        return utils.dump_datablock(pointer, 1)
    
    def resolve(self):
        assert(self.buffer)      
        self.pointer = bpy.data.cameras.get(self.buffer['name'])
    
    def diff(self):
        d = diff(self.dump(pointer=self.pointer),self.buffer)
        print(d)
        return len(d)>1

bl_id = "cameras"
bl_class = bpy.types.Camera
bl_rep_class = BlCamera
bl_delay_refresh = 1
bl_delay_apply = 1
