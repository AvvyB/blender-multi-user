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
    bl_check_common = False
    bl_icon = 'CAMERA_DATA'
    bl_reload_parent = False

    def _construct(self, data):
        return bpy.data.cameras.new(data["name"])


    def _load_implementation(self, data, target):
        loader = Loader()       
        loader.load(target, data)

        dof_settings = data.get('dof')
        
        # DOF settings
        if dof_settings:
            loader.load(target.dof, dof_settings)

        background_images = data.get('background_images')

        target.background_images.clear()
        
        if background_images:
            for img_name, img_data in background_images.items():
                img_id = img_data.get('image')
                if img_id:
                    target_img = target.background_images.new()
                    target_img.image = bpy.data.images[img_id]
                    loader.load(target_img, img_data)

    def _dump_implementation(self, data, instance=None):
        assert(instance)

        # TODO: background image support
        
        dumper = Dumper()
        dumper.depth = 3
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
            'ortho_scale',
            'aperture_ratio',
            'display_size',
            'show_limits',
            'show_mist',
            'show_sensor',
            'show_name',
            'sensor_fit',
            'sensor_height',
            'sensor_width',
            'show_background_images',
            'background_images',
            'alpha',
            'display_depth',
            'frame_method',
            'offset',
            'rotation',
            'scale',
            'use_flip_x',
            'use_flip_y',
            'image'
        ]
        return dumper.dump(instance)
    
    def _resolve_deps_implementation(self):
        deps = []
        for background in self.instance.background_images:
            if background.image:
                deps.append(background.image)
        
        return deps
