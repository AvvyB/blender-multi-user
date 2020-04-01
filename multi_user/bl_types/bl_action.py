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
import copy
import numpy as np
from enum import Enum

from .. import utils
from ..libs.dump_anything import (
    Dumper, Loader, np_dump_collection, np_load_collection, remove_items_from_dict)
from .bl_datablock import BlDatablock


KEYFRAME = [
    'amplitude',
    'co',
    'back',
    'handle_left',
    'handle_right',
    'easing',
    'handle_left_type',
    'handle_right_type',
    'type',
    'interpolation',
]


def dump_fcurve(fcurve: bpy.types.FCurve, use_numpy:bool =True) -> dict:
    """ Dump a sigle curve to a dict

        :arg fcurve: fcurve to dump
        :type fcurve: bpy.types.FCurve
        :arg use_numpy: use numpy to eccelerate dump
        :type use_numpy: bool
        :return: dict
    """
    fcurve_data = {
        "data_path": fcurve.data_path,
        "dumped_array_index": fcurve.array_index,
        "use_numpy": use_numpy
    }

    if use_numpy:
        points = fcurve.keyframe_points
        fcurve_data['keyframes_count']  = len(fcurve.keyframe_points)
        fcurve_data['keyframe_points'] = np_dump_collection(points, KEYFRAME)

    else:  # Legacy method
        dumper = Dumper()
        fcurve_data["keyframe_points"] = []

        for k in fcurve.keyframe_points:
            fcurve_data["keyframe_points"].append(
                dumper.dump(k)
            )

    return fcurve_data


def load_fcurve(fcurve_data, fcurve):
    """ Load a dumped fcurve

        :arg fcurve_data: a dumped fcurve
        :type fcurve_data: dict
        :arg fcurve: fcurve to dump
        :type fcurve: bpy.types.FCurve
    """
    use_numpy = fcurve_data.get('use_numpy')

    keyframe_points = fcurve.keyframe_points

    # Remove all keyframe points
    for i in range(len(keyframe_points)):
        keyframe_points.remove(keyframe_points[0], fast=True)

    if use_numpy:
        keyframe_points.add(fcurve_data['keyframes_count'])
        np_load_collection(fcurve_data["keyframe_points"], keyframe_points, KEYFRAME)

    else:
        # paste dumped keyframes
        for dumped_keyframe_point in fcurve_data["keyframe_points"]:
            if dumped_keyframe_point['type'] == '':
                dumped_keyframe_point['type'] = 'KEYFRAME'

            new_kf = keyframe_points.insert(
                dumped_keyframe_point["co"][0],
                dumped_keyframe_point["co"][1],
                options={'FAST', 'REPLACE'}
            )

            keycache = copy.copy(dumped_keyframe_point)
            keycache = remove_items_from_dict(
                keycache,
                ["co", "handle_left", "handle_right", 'type']
            )

            loader = Loader()
            loader.load(new_kf, keycache)

            new_kf.type = dumped_keyframe_point['type']
            new_kf.handle_left = [
                dumped_keyframe_point["handle_left"][0],
                dumped_keyframe_point["handle_left"][1]
            ]
            new_kf.handle_right = [
                dumped_keyframe_point["handle_right"][0],
                dumped_keyframe_point["handle_right"][1]
            ]

            fcurve.update()


class BlAction(BlDatablock):
    bl_id = "actions"
    bl_class = bpy.types.Action
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'ACTION_TWEAK'

    def _construct(self, data):
        return bpy.data.actions.new(data["name"])

    def _load(self, data, target):
        for dumped_fcurve in data["fcurves"]:
            dumped_data_path = dumped_fcurve["data_path"]
            dumped_array_index = dumped_fcurve["dumped_array_index"]

            # create fcurve if needed
            fcurve = target.fcurves.find(
                dumped_data_path, index=dumped_array_index)
            if fcurve is None:
                fcurve = target.fcurves.new(
                    dumped_data_path, index=dumped_array_index)

            load_fcurve(dumped_fcurve, fcurve)
        target.id_root = data['id_root']

    def _dump(self, pointer=None):
        assert(pointer)
        dumper = Dumper()
        dumper.exclude_filter = [
            'name_full',
            'original',
            'use_fake_user',
            'user',
            'is_library_indirect',
            'select_control_point',
            'select_right_handle',
            'select_left_handle',
            'uuid',
            'users'
        ]
        dumper.depth = 1
        data = dumper.dump(pointer)

        data["fcurves"] = []

        for fcurve in self.pointer.fcurves:
            data["fcurves"].append(dump_fcurve(fcurve, use_numpy=True))

        return data
