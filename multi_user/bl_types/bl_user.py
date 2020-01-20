import bpy
import mathutils
import jsondiff

from .. import utils
from .. import presence
from .bl_datablock import BlDatablock
from ..libs.replication.replication.constants import UP


class BlUser(BlDatablock):
    bl_id = "users"
    bl_class = presence.User
    bl_delay_refresh = .1
    bl_delay_apply = .1
    bl_automatic_push = True
    bl_icon = 'CON_ARMATURE'

    def construct(self, data):
        user = bpy.data.window_managers['WinMan'].online_users.add()
        user.name = data['name']
        user.username = data['name']
        user.current_frame = data['current_frame']

    def apply(self):
        if self.pointer is None:
            self.set_pointer()

        self.load(self.data,self.pointer)

        for obj in bpy.data.objects:
            if obj.hide_select and obj.uuid not in self.data['selected_objects']:
                obj.hide_select = False
            elif not obj.hide_select and obj.uuid in self.data['selected_objects']:
                obj.hide_select = True

        presence.refresh_3d_view()

        self.state = UP

    def load(self, data, target):
        target.current_frame = data['current_frame']

    def dump(self, pointer=None):
        data = utils.dump_anything.dump(pointer)
        data['location'] = pointer.location
        data['color'] = pointer.color
        data['selected_objects'] = pointer.selected_objects
        data['view_matrix'] = pointer.view_matrix
        data['current_frame'] = bpy.context.scene.frame_current

        return data

    def update(self):
        self.pointer.is_dirty = True
    
    def resolve(self):
        self.pointer = bpy.data.window_managers['WinMan'].online_users.get(self.data['name'])

    def is_valid(self):
        return True



