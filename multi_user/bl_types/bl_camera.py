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


class BlCamera(BlDatablock):
    bl_id = "cameras"
    bl_class = bpy.types.Camera
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'CAMERA_DATA'

    def _construct(self, data):
        return bpy.data.cameras.new(data["name"])


    def _load_implementation(self, data, target):
        loader = Loader()
        loader.load(target, data)

        dof_settings = data.get('dof')
        
        # DOF settings
        if dof_settings:
            loader.load(target.dof, dof_settings)

    def _dump_implementation(self, data, instance=None):
        assert(instance)

        # TODO: background image support
        
        dumper = Dumper()
        dumper.depth = 2
        dumper.include_filter = [
            "name",
            'type',
            'lens',
            'lens_unit',
            'shift_x',
            'shift_y',
            'clip_start',
            'clip_end',
            'dof',
            'use_dof',
            'sensor_fit',
            'sensor_width',
            'focus_object',
            'focus_distance',
            'aperture_fstop',
            'aperture_blades',
            'aperture_rotation',
            'aperture_ratio',
            'display_size',
            'show_limits',
            'show_mist',
            'show_sensor',
            'show_name',
            'sensor_fit',
            'sensor_height',
            'sensor_width',
        ]
        return dumper.dump(instance)
    

