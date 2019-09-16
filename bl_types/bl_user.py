import bpy
import mathutils

from .. import utils
from .. import presence
from .bl_datablock import BlDatablock
from ..libs.replication.replication.constants import UP
from ..libs.debug import draw_point



class BlUser(BlDatablock):
    # def __init__(self, *args, **kwargs):
    #     super().__init__( *args, **kwargs)
    
    #     if self.buffer:
    #         self.load(self.buffer, self.pointer)

    def construct(self, name):
        return presence.User()
    
    def load(self, data, target):      
        target.name = data['name']
        target.location = data['location']
        target.selected_objects = data['selected_objects']
        utils.dump_anything.load(target, data)
    
    def apply(self):
        if self.pointer is None:
            self.pointer = self.construct(self.buffer)

        if self.pointer:
            self.load(data=self.buffer, target=self.pointer)
        
        self.state = UP
        #TODO: refactor in order to redraw in cleaner ways
        if presence.renderer:
            presence.renderer.draw_client_camera(self.buffer['name'], self.buffer['location'],self.buffer['color'])
            presence.renderer.draw_client_selection(self.buffer['name'], self.buffer['color'],self.buffer['selected_objects'])
            presence.refresh_3d_view()


    def dump(self,pointer=None):
        data = utils.dump_anything.dump(pointer)
        data['location'] = pointer.location
        data['color'] = pointer.color
        data['selected_objects'] = pointer.selected_objects
        return data


    def diff(self):
        if self.pointer.is_dirty:
            self.pointer.is_dirty = False
            return True

        for i,coord in enumerate(self.pointer.location):
            if coord != self.buffer['location'][i]:
                return True
        return False

bl_id = "users"
bl_class = presence.User
bl_rep_class = BlUser 
bl_delay_refresh = .2
bl_delay_apply = .2
bl_automatic_push = True
bl_icon = 'CON_ARMATURE'