# ##### BEGIN GPL LICENSE BLOCK #####
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


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

    def _construct(self, data):
        type = 'CUBE' if data['type'] == 'CUBEMAP' else data['type']
        # See https://developer.blender.org/D6396
        if bpy.app.version[1] >= 83:
            return bpy.data.lightprobes.new(data["name"], type)
        else:
            logger.warning("Lightprobe replication only supported since 2.83. See https://developer.blender.org/D6396")

    def _load_implementation(self, data, target):
        utils.dump_anything.load(target, data)

    def _dump_implementation(self, data, pointer=None):
        assert(pointer)
        if bpy.app.version[1] < 83:
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



