import bpy
import mathutils
from jsondiff import diff

from .. import utils
from .bl_datablock import BlDatablock


class BlLight(BlDatablock):
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

    def diff(self):
        return (self.bl_diff() or
                len(diff(self.dump(pointer=self.pointer), self.buffer)) > 1)

    def is_valid(self):
        return bpy.data.lights.get(self.buffer['name'])

bl_id = "lights"
bl_class = bpy.types.Light
bl_rep_class = BlLight
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'LIGHT_DATA'