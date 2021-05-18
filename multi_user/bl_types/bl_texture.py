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
from replication.protocol import ReplicatedDatablock


class BlTexture(ReplicatedDatablock):
    bl_id = "textures"
    bl_class = bpy.types.Texture
    bl_check_common = False
    bl_icon = 'TEXTURE'
    bl_reload_parent = False

    def load(data: dict, datablock: object):
        loader = Loader()
        loader.load(target, data)

    def construct(data: dict) -> object:
        return bpy.data.textures.new(data["name"], data["type"])

    def dump(datablock: object) -> dict:
        assert(instance)

        dumper = Dumper()
        dumper.depth = 1
        dumper.exclude_filter = [
            'tag',
            'original',
            'users',
            'uuid',
            'is_embedded_data',
            'is_evaluated',
            'name_full'
        ]

        data = dumper.dump(instance)
        color_ramp = getattr(instance, 'color_ramp', None)

        if color_ramp:
            dumper.depth = 4
            data['color_ramp'] = dumper.dump(color_ramp)

        return data

    def resolve_deps(datablock: object) -> [object]:
        # TODO: resolve material
        deps = []

        image = getattr(self.instance,"image", None)

        if image:
            deps.append(image)

        return deps


