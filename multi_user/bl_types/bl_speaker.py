import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock


class BlSpeaker(BlDatablock):
    bl_id = "speakers"
    bl_class = bpy.types.Speaker
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'SPEAKER'

    def load_implementation(self, data, target):
        utils.dump_anything.load(target, data)

    def construct(self, data):
        return bpy.data.speakers.new(data["name"])

    def dump_implementation(self, data, pointer=None):
        assert(pointer)

        dumper = utils.dump_anything.Dumper()
        dumper.depth = 1
        dumper.include_filter = [
            "muted",
            'volume',
            'name',
            'pitch',
            'volume_min',
            'volume_max',
            'attenuation',
            'distance_max',
            'distance_reference',
            'cone_angle_outer',
            'cone_angle_inner',
            'cone_volume_outer'
        ]

        return dumper.dump(pointer)

    def resolve_deps_implementation(self):
        return []


