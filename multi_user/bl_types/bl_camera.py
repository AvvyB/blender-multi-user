from jsondiff import diff

import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock


class BlCamera(BlDatablock):
    def load(self, data, target):
        utils.dump_anything.load(target, data)

        dof_settings = data.get('dof')
        
        # DOF settings
        if dof_settings:
            utils.dump_anything.load(target.dof, dof_settings)

    def construct(self, data):
        return bpy.data.cameras.new(data["name"])

    def dump(self, pointer=None):
        assert(pointer)

        dumper = utils.dump_anything.Dumper()
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
        ]
        return dumper.dump(pointer)

    def resolve(self):
        assert(self.buffer)
        self.pointer = bpy.data.cameras.get(self.buffer['name'])

    def diff(self):
        return (self.bl_diff() or
                len(diff(self.dump(pointer=self.pointer), self.buffer)))

    def is_valid(self):
        return bpy.data.cameras.get(self.buffer['name'])


bl_id = "cameras"
bl_class = bpy.types.Camera
bl_rep_class = BlCamera
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'CAMERA_DATA'
