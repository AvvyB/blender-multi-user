import bpy
import mathutils

from .. import utils
from ..libs.replication.data import ReplicatedDatablock

class BlLight(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        self.icon = 'LIGHT_DATA'

        super().__init__( *args, **kwargs)
        
    def load(self, data, target):
        if target is None:
            target = bpy.data.lights.new(data["name"], data["type"])

        utils.dump_anything.load(target, data)


    def dump(self, pointer=None):
        assert(pointer)
        
        return utils.dump_datablock(pointer, 3)

bl_id = "lights"
bl_class = bpy.types.Light
bl_rep_class = BlLight

