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

from ..libs.dump_anything import Dumper, Loader, np_dump_collection, np_load_collection
from .bl_datablock import BlDatablock

POINT = ['co', 'weight_softbody', 'co_deform']


class BlLattice(BlDatablock):
    bl_id = "lattices"
    bl_class = bpy.types.Lattice
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'LATTICE_DATA'

    def _load_implementation(self, data, target):
        loader = Loader()
        loader.load(target, data)

        np_load_collection(data['points'], target.points, POINT)

    def _construct(self, data):
        return bpy.data.lattices.new(data["name"])

    def _dump_implementation(self, data, pointer=None):
        assert(pointer)

        dumper = Dumper()
        dumper.depth = 1
        dumper.include_filter = [
            "name",
            'type',
            'points_u',
            'points_v',
            'points_w',
            'interpolation_type_u',
            'interpolation_type_v',
            'interpolation_type_w',
            'use_outside'
        ]
        data = dumper.dump(pointer)

        data['points'] = np_dump_collection(pointer.points, POINT)
        return data

