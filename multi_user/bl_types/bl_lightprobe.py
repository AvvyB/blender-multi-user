import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock


class BlLightProbe(BlDatablock):
    def load(self, data, target):
        utils.dump_anything.load(target, data)

    def construct(self, data):
        return bpy.data.lightprobes.new(data["name"])

    def dump(self, pointer=None):
        assert(pointer)

        dumper = utils.dump_anything.Dumper()
        dumper.depth = 1
        dumper.include_filter = [
            "name",
            'influence_type',
            'influence_distance',
            'falloff',
            'intensity',
            'clip_start',
            'clip_end',
            'visibility_collection',
            'use_custom_parallax',
            'parallax_type',
            'parallax_distance',
        ]

        return dumper.dump(pointer)

    def resolve(self):
        self.pointer = utils.find_from_attr('uuid', self.uuid, bpy.data.lattices)

    def is_valid(self):
        return bpy.data.lattices.get(self.data['name'])


bl_id = "lightprobes"
bl_class = bpy.types.LightProbe
bl_rep_class = BlLightProbe
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'LIGHTPROBE_GRID'
