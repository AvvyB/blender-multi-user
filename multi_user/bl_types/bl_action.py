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
import logging
import numpy as np
from enum import Enum

from .. import utils
from .bl_datablock import BlDatablock

logger = logging.getLogger(__name__)

ENUM_EASING_TYPE = [
    'AUTO',
    'EAS_IN',
    'EASE_OUT',
    'EASE_IN_OUT']

ENUM_HANDLE_TYPE = [
    'FREE',
    'ALIGNED',
    'VECTOR',
    'AUTO',
    'AUTO_CLAMPED']

ENUM_INTERPOLATION_TYPE = [
    'CONSTANT',
    'LINEAR',
    'BEZIER',
    'SINE',
    'QUAD',
    'CUBIC',
    'QUART',
    'QUINT',
    'EXPO',
    'CIRC',
    'BACK',
    'BOUNCE',
    'ELASTIC']

ENUM_KEY_TYPE = [
    'KEYFRAME',
    'BREAKDOWN',
    'MOVING_HOLD',
    'EXTREME',
    'JITTER']

#TODO: Automatic enum and numpy dump and loading

def dump_fcurve(fcurve, use_numpy=True):
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
        keyframes_count = len(fcurve.keyframe_points)

        k_amplitude = np.empty(keyframes_count, dtype=np.float64)
        fcurve.keyframe_points.foreach_get('amplitude', k_amplitude)
        k_co = np.empty(keyframes_count*2, dtype=np.float64)
        fcurve.keyframe_points.foreach_get('co', k_co)
        k_back = np.empty(keyframes_count, dtype=np.float64)
        fcurve.keyframe_points.foreach_get('back', k_back)
        k_handle_left = np.empty(keyframes_count*2, dtype=np.float64)
        fcurve.keyframe_points.foreach_get('handle_left', k_handle_left)
        k_handle_right = np.empty(keyframes_count*2, dtype=np.float64)
        fcurve.keyframe_points.foreach_get('handle_right', k_handle_right)

        fcurve_data['amplitude'] = k_amplitude.tobytes()
        fcurve_data['co'] = k_co.tobytes()
        fcurve_data['back'] = k_back.tobytes()
        fcurve_data['handle_left'] = k_handle_left.tobytes()
        fcurve_data['handle_right'] = k_handle_right.tobytes()

        fcurve_data['easing'] = [ENUM_EASING_TYPE.index(p.easing) for p in fcurve.keyframe_points]
        fcurve_data['handle_left_type'] = [ENUM_HANDLE_TYPE.index(p.handle_left_type) for p in fcurve.keyframe_points]
        fcurve_data['handle_right_type'] = [ENUM_HANDLE_TYPE.index(p.handle_right_type) for p in fcurve.keyframe_points]
        fcurve_data['type'] = [ENUM_KEY_TYPE.index(p.type) for p in fcurve.keyframe_points]
        fcurve_data['interpolation'] = [ENUM_INTERPOLATION_TYPE.index(p.interpolation) for p in fcurve.keyframe_points]

    else: # Legacy method
        dumper = utils.dump_anything.Dumper()
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
        k_amplitude = np.frombuffer(fcurve_data['amplitude'], dtype=np.float64)

        keyframe_count = len(k_amplitude)

        k_co = np.frombuffer(fcurve_data['co'], dtype=np.float64)
        k_back = np.frombuffer(fcurve_data['back'], dtype=np.float64)
        k_amplitude = np.frombuffer(fcurve_data['amplitude'], dtype=np.float64)
        k_handle_left= np.frombuffer(fcurve_data['handle_left'], dtype=np.float64)
        k_handle_right= np.frombuffer(fcurve_data['handle_right'], dtype=np.float64)

        keyframe_points.add(keyframe_count)

        keyframe_points.foreach_set('co',k_co)
        keyframe_points.foreach_set('back',k_back)
        keyframe_points.foreach_set('amplitude',k_amplitude)
        keyframe_points.foreach_set('handle_left',k_handle_left)
        keyframe_points.foreach_set('handle_right',k_handle_right)

        for index, point in enumerate(keyframe_points):
            point.type = ENUM_KEY_TYPE[fcurve_data['type'][index]]
            point.easing = ENUM_EASING_TYPE[fcurve_data['easing'][index]]
            point.handle_left_type = ENUM_HANDLE_TYPE[fcurve_data['handle_left_type'][index]]
            point.handle_right_type = ENUM_HANDLE_TYPE[fcurve_data['handle_right_type'][index]]
            point.interpolation = ENUM_INTERPOLATION_TYPE[fcurve_data['interpolation'][index]]

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
            keycache = utils.dump_anything.remove_items_from_dict(
                keycache,
                ["co", "handle_left", "handle_right", 'type']
            )

            utils.dump_anything.load(new_kf, keycache)

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
            fcurve = target.fcurves.find(dumped_data_path, index=dumped_array_index)
            if fcurve is None:
                fcurve = target.fcurves.new(dumped_data_path, index=dumped_array_index)

            load_fcurve(dumped_fcurve, fcurve)
        target.id_root = data['id_root']

    def _dump(self, pointer=None):
        start = utils.current_milli_time()
        assert(pointer)
        dumper = utils.dump_anything.Dumper()
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

        logger.error(
            f"{self.pointer.name} dumping time: {utils.current_milli_time()-start} ms")
        return data

