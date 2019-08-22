import bpy
import mathutils

from .. import utils
from ..libs.replication.data import ReplicatedDatablock

class BlLight(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        self.icon = 'LIGHT_DATA'

        super().__init__( *args, **kwargs)
    
    def construct(self, data):
        return bpy.data.lights.new(data["name"], data["type"])
    
    def load(self, data, target):
        utils.dump_anything.load(target, data)


    def dump(self, pointer=None):
        assert(pointer)
        
        return utils.dump_datablock(pointer, 3)
    
    def resolve(self):
        assert(self.buffer)      
        self.pointer = bpy.data.lights.get(self.buffer['name'])
        
bl_id = "lights"
bl_class = bpy.types.Light
bl_rep_class = BlLight
bl_delay_refresh = 1
bl_delay_apply = 1
