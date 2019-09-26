import bpy
import mathutils
from jsondiff import diff

from .. import utils
from .bl_datablock import BlDatablock


class BlMetaball(BlDatablock):
    def construct(self, data):
        return bpy.data.metaballs.new(data["name"])

    def load(self, data, target):
        utils.dump_anything.load(target, data)
        
        target.elements.clear()
        for element in data["elements"]:
            new_element = target.elements.new(type=data["elements"][element]['type'])
            utils.dump_anything.load(new_element, data["elements"][element])

    def dump(self, pointer=None):
        assert(pointer)
        dumper = utils.dump_anything.Dumper()
        dumper.depth = 3
        dumper.exclude_filter = ["is_editmode"]

        data = dumper.dump(pointer)
        return data

    def resolve(self):
        assert(self.buffer)
        self.pointer = bpy.data.metaballs.get(self.buffer['name'])

    def diff(self):
        rev = diff(self.dump(pointer=self.pointer), self.buffer)
        print(rev)
        return (self.bl_diff() or
                len(rev) > 0)

    def is_valid(self):
        return bpy.data.metaballs.get(self.buffer['name'])

bl_id = "metaballs"
bl_class = bpy.types.MetaBall
bl_rep_class = BlMetaball
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'META_BALL'