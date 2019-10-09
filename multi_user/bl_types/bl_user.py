import bpy
import mathutils

from .. import utils
from .. import presence
from .bl_datablock import BlDatablock
from ..libs.replication.replication.constants import UP

class BlUser(BlDatablock):
    def construct(self, name):
        return presence.User()
    
    def load(self, data, target):      
        target.name = data['name']
        target.location = data['location']
        target.selected_objects = data['selected_objects']
        utils.dump_anything.load(target, data)
    
    def apply(self):
        # super().apply()
    #     self.data = jsondiff.patch(self.data, self.modifications, marshal=True)
    #     self.modifications = None
        
        if self.pointer:
            self.load(data=self.data, target=self.pointer)

    #     settings = bpy.context.window_manager.session

        presence.refresh_3d_view()
        
        self.state = UP




    def dump(self,pointer=None):
        data = utils.dump_anything.dump(pointer)
        data['location'] = pointer.location
        data['color'] = pointer.color
        data['selected_objects'] = pointer.selected_objects
        return data
    
    def update(self):
        self.pointer.is_dirty = True

    # def diff(self):
    #     if not self.pointer:
    #         return False
    #     if self.pointer.is_dirty:
    #         self.pointer.is_dirty = False
    #         return True

    #     for i,coord in enumerate(self.pointer.location):
    #         if coord != self.data['location'][i]:
    #             return True
    #     return False

    def is_valid(self):
        return True
bl_id = "users"
bl_class = presence.User
bl_rep_class = BlUser 
bl_delay_refresh = .1
bl_delay_apply = .1
bl_automatic_push = True
bl_icon = 'CON_ARMATURE'