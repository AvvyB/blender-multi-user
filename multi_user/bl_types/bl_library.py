import bpy
import mathutils

from ..libs import dump_anything
from .bl_datablock import BlDatablock


class BlLibrary(BlDatablock):
    bl_id = "libraries"
    bl_class = bpy.types.Library
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'LIBRARY_DATA_DIRECT'

    def construct(self, data):
        with bpy.data.libraries.load(filepath=data["filepath"], link=True) as (sourceData, targetData):
            targetData = sourceData
            return sourceData
    def load(self, data, target):
        pass

    def dump(self, pointer=None):
        assert(pointer)
        return dump_anything.dump(pointer, 1)


