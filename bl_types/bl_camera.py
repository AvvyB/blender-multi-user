import bpy
import mathutils

from .. import utils
from ..libs.replication.data import ReplicatedDatablock

class BlCamera(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        self.icon = 'CAMERA_DATA'

        super().__init__( *args, **kwargs)
        
    def load(self, data, target):
        if target is None:
            target = bpy.data.cameras.new(data["name"])

        utils.dump_anything.load(target, data)


    def dump(self, pointer=None):
        assert(pointer)
        
        return utils.dump_datablock(pointer, 1)

bl_id = "cameras"
bl_class = bpy.types.Camera
bl_rep_class = BlCamera

