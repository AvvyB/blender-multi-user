import bpy
import mathutils

from .. import utils
from ..libs.replication.replication.constants import (DIFF_JSON)
from .bl_datablock import BlDatablock


class BlParticle(BlDatablock):
    bl_id = "particles"
    bl_class = bpy.types.ParticleSettings
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'PARTICLES'

    diff_method = DIFF_JSON

    def construct(self, data):
        return bpy.data.particles.new(data["name"])

    def load_implementation(self, data, target):
        utils.dump_anything.load(target, data)

    def dump_implementation(self, data, pointer=None):
        assert(pointer)

        dumper = utils.dump_anything.Dumper()
        dumper.depth = 1
        data = dumper.dump(pointer)

        return data
