import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock


class BlMetaball(BlDatablock):
    bl_id = "metaballs"
    bl_class = bpy.types.MetaBall
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'META_BALL'

    def _construct(self, data):
        return bpy.data.metaballs.new(data["name"])

    def load(self, data, target):
        utils.dump_anything.load(target, data)
        
        target.elements.clear()
        for element in data["elements"]:
            new_element = target.elements.new(type=data["elements"][element]['type'])
            utils.dump_anything.load(new_element, data["elements"][element])

    def dump_implementation(self, data, pointer=None):
        assert(pointer)
        dumper = utils.dump_anything.Dumper()
        dumper.depth = 3
        dumper.exclude_filter = ["is_editmode"]

        data = dumper.dump(pointer)
        return data



