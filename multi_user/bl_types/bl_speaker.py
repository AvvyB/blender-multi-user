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


class BlSpeaker(ReplicatedDatablock):
    bl_id = "speakers"
    bl_class = bpy.types.Speaker
    bl_check_common = False
    bl_icon = 'SPEAKER'
    bl_reload_parent = False

    def load(data: dict, datablock: object):
        loader = Loader()
        loader.load(target, data)

    def construct(data: dict) -> object:
        return bpy.data.speakers.new(data["name"])

    def dump(datablock: object) -> dict:
        assert(instance)

        dumper = Dumper()
        dumper.depth = 1
        dumper.include_filter = [
            "muted",
            'volume',
            'name',
            'pitch',
            'sound',
            'volume_min',
            'volume_max',
            'attenuation',
            'distance_max',
            'distance_reference',
            'cone_angle_outer',
            'cone_angle_inner',
            'cone_volume_outer'
        ]

        return dumper.dump(instance)

    def resolve_deps(datablock: object) -> [object]:
        # TODO: resolve material
        deps = []

        sound = self.instance.sound

        if sound:
            deps.append(sound)

        return deps


