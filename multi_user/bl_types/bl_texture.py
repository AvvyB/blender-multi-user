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


class BlTexture(BlDatablock):
    bl_id = "textures"
    bl_class = bpy.types.Texture
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = False
    bl_icon = 'TEXTURE'

    def _load_implementation(self, data, target):
        loader = Loader()
        loader.load(target, data)

    def _construct(self, data):
        return bpy.data.textures.new(data["name"], data["type"])

    def _dump_implementation(self, data, instance=None):
        assert(instance)

        dumper = Dumper()
        dumper.depth = 1
        dumper.exclude_filter = []

        data = dumper.dump(instance)
        color_ramp = getattr(instance, 'color_ramp', None)

        if color_ramp:
            dumper.depth = 4
            data['color_ramp'] = dumper.dump(color_ramp)

        return data

    def _resolve_deps_implementation(self):
        # TODO: resolve material
        deps = []

        image = getattr(self.instance,"image", None)

        if image:
            deps.append(image)

        return deps


