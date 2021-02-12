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

from .dump_anything import Loader, Dumper
from .bl_datablock import BlDatablock


class BlLight(BlDatablock):
    bl_id = "lights"
    bl_class = bpy.types.Light
    bl_check_common = False
    bl_icon = 'LIGHT_DATA'
    bl_reload_parent = False

    def _construct(self, data):
        return bpy.data.lights.new(data["name"], data["type"])

    def _load_implementation(self, data, target):
        loader = Loader()
        loader.load(target, data)

    def _dump_implementation(self, data, instance=None):
        assert(instance)
        dumper = Dumper()
        dumper.depth = 3
        dumper.include_filter = [
            "name",
            "type",
            "color",
            "energy",
            "specular_factor",
            "uuid",
            "shadow_soft_size",
            "use_custom_distance",
            "cutoff_distance",
            "use_shadow",
            "shadow_buffer_clip_start",
            "shadow_buffer_soft",
            "shadow_buffer_bias",
            "shadow_buffer_bleed_bias",
            "contact_shadow_distance",
            "contact_shadow_soft_size",
            "contact_shadow_bias",
            "contact_shadow_thickness",
            "shape",
            "size_y",
            "size",
            "angle",
            'spot_size',
            'spot_blend'
        ]
        data = dumper.dump(instance)
        return data




