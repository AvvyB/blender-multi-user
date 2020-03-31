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
import logging

from .. import utils
from .bl_datablock import BlDatablock
from ..libs.dump_anything import (Dumper, Loader,
                                  np_load_collection,
                                  np_dump_collection)

logger = logging.getLogger(__name__)

SPLINE_BEZIER_POINT = [
    # "handle_left_type",
    # "handle_right_type",
    "handle_left",
    "co",
    "handle_right",
    "tilt",
    "weight_softbody",
    "radius",
]

SPLINE_POINT = [
    "co",
    "tilt",
    "weight_softbody",
    "radius",
]

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
        loader = Loader()
        loader.load(target, data)

        target.splines.clear()
        # load splines
        for spline in data['splines'].values():
            new_spline = target.splines.new(spline['type'])
            

            # Load curve geometry data
            if new_spline.type == 'BEZIER':
                bezier_points = new_spline.bezier_points 
                bezier_points.add(spline['bezier_points_count'])
                np_load_collection(spline['bezier_points'], bezier_points, SPLINE_BEZIER_POINT)
                
            # Not really working for now...
            # See https://blender.stackexchange.com/questions/7020/create-nurbs-surface-with-python
            if new_spline.type == 'NURBS':
                logger.error("NURBS not supported.")
            #     new_spline.points.add(len(data['splines'][spline]["points"])-1)
            #     for point_index in data['splines'][spline]["points"]:
            #         loader.load(
            #             new_spline.points[point_index], data['splines'][spline]["points"][point_index])

            loader.load(new_spline, spline)
    def _dump_implementation(self, data, pointer=None):
        assert(pointer)
        dumper = Dumper()

        data = dumper.dump(pointer)
        data['splines'] = {}

        for index, spline in enumerate(pointer.splines):
            dumper.depth = 2
            spline_data = dumper.dump(spline)
            # spline_data['points'] = np_dump_collection(spline.points, SPLINE_POINT)
            spline_data['bezier_points_count'] = len(spline.bezier_points)-1
            spline_data['bezier_points'] = np_dump_collection(spline.bezier_points, SPLINE_BEZIER_POINT)
            data['splines'][index] = spline_data

        if isinstance(pointer, T.SurfaceCurve):
            data['type'] = 'SURFACE'
        elif isinstance(pointer, T.TextCurve):
            data['type'] = 'FONT'
        elif isinstance(pointer, T.Curve):
            data['type'] = 'CURVE'
        return data
