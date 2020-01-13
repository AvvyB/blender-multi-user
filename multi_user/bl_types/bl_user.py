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

    def construct(self, name):
        return presence.User()

    def apply(self):
        for obj in bpy.data.objects:
            if obj.hide_select and obj.uuid not in self.data['selected_objects']:
                obj.hide_select = False
            elif not obj.hide_select and obj.uuid in self.data['selected_objects']:
                obj.hide_select = True

        presence.refresh_3d_view()

        self.state = UP

    def dump(self, pointer=None):
        data = utils.dump_anything.dump(pointer)
        data['location'] = pointer.location
        data['color'] = pointer.color
        data['selected_objects'] = pointer.selected_objects
        data['view_matrix'] = pointer.view_matrix

        return data

    def update(self):
        self.pointer.is_dirty = True

    def is_valid(self):
        return True



