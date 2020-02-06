import bpy
import mathutils
import logging

from .. import utils
from .bl_datablock import BlDatablock

logger = logging.getLogger(__name__)

class BlLightprobe(BlDatablock):
    bl_id = "lightprobes"
    bl_class = bpy.types.LightProbe
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'LIGHTPROBE_GRID'

    def load(self, data, target):
        utils.dump_anything.load(target, data)

    def construct(self, data):
        type = 'CUBE' if data['type'] == 'CUBEMAP' else data['type']
        # See https://developer.blender.org/D6396
        if bpy.app.version[1] >= 83:
            return bpy.data.lightprobes.new(data["name"], type)
        else:
            logger.warning("Lightprobe replication only supported since 2.83. See https://developer.blender.org/D6396")

        
        

    def dump(self, pointer=None):
        assert(pointer)
        if bpy.app.version[1] < 84:
            logger.warning("Lightprobe replication only supported since 2.83. See https://developer.blender.org/D6396")

        dumper = utils.dump_anything.Dumper()
        dumper.depth = 1
        dumper.include_filter = [
            "name",
            'type',
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
            'grid_resolution_x',
            'grid_resolution_y',
            'grid_resolution_z',
            'visibility_buffer_bias',
            'visibility_bleed_bias',
            'visibility_blur'
        ]

        return dumper.dump(pointer)

    def is_valid(self):
        return bpy.data.lattices.get(self.data['name'])
