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
import bpy.types as T
import mathutils

from .. import utils
from .bl_datablock import BlDatablock
from ..libs import dump_anything


class BlCurve(BlDatablock):
    bl_id = "curves"
    bl_class = bpy.types.Curve
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'CURVE_DATA'

    def _construct(self, data):
        return bpy.data.curves.new(data["name"], data["type"])

    def _load_implementation(self, data, target):
        dump_anything.load(target, data)

        target.splines.clear()
        # load splines
        for spline in data['splines']:
            new_spline = target.splines.new(data['splines'][spline]['type'])
            dump_anything.load(new_spline, data['splines'][spline])
            
            # Load curve geometry data
            if new_spline.type == 'BEZIER':
                for bezier_point_index in data['splines'][spline]["bezier_points"]:
                    if bezier_point_index != 0:
                        new_spline.bezier_points.add(1)
                    dump_anything.load(
                        new_spline.bezier_points[bezier_point_index], data['splines'][spline]["bezier_points"][bezier_point_index])
            
            # Not really working for now...
            # See https://blender.stackexchange.com/questions/7020/create-nurbs-surface-with-python
            if new_spline.type == 'NURBS':
                new_spline.points.add(len(data['splines'][spline]["points"])-1)
                for point_index in data['splines'][spline]["points"]:
                    dump_anything.load(
                        new_spline.points[point_index], data['splines'][spline]["points"][point_index])

    def _dump_implementation(self, data, pointer=None):
        assert(pointer)
        dumper = dump_anything.Dumper()

        data = dumper.dump(pointer)
        data['splines'] = {}

        dumper = utils.dump_anything.Dumper()
        dumper.depth = 3

        for index, spline in enumerate(pointer.splines):
            spline_data = dump_anything.dump(spline)
            spline_data['points'] = dumper.dump(spline.points)
            spline_data['bezier_points'] = dumper.dump(spline.bezier_points)
            spline_data['type'] = dumper.dump(spline.type)
            data['splines'][index] = spline_data

        
        if isinstance(pointer, T.SurfaceCurve):
            data['type'] = 'SURFACE'
        elif isinstance(pointer, T.TextCurve):
            data['type'] = 'FONT'
        elif isinstance(pointer, T.Curve):
            data['type'] = 'CURVE'
        return data

