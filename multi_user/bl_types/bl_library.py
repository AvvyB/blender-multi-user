import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock


class BlLibrary(BlDatablock):
    def construct(self, data):
        with bpy.data.libraries.load(filepath=data["filepath"], link=True) as (sourceData, targetData):
            targetData = sourceData
            return sourceData
    def load(self, data, target):
        pass

    def dump(self, pointer=None):
        assert(pointer)
        return utils.dump_datablock(pointer, 1)

    def resolve(self):
        assert(self.data)
        self.pointer = bpy.data.libraries.get(self.data['name'])

    # def diff(self):
    #     return (self.bl_diff())

    def is_valid(self):
        return bpy.data.libraries.get(self.data['name'])

bl_id = "libraries"
bl_class = bpy.types.Library
bl_rep_class = BlLibrary
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'LIBRARY_DATA_DIRECT'