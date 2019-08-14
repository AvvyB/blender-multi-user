import bpy
import mathutils

from .. import utils
from .. import presence
from ..libs.replication.data import ReplicatedDatablock
from ..libs.replication.constants import UP
from ..libs.debug import draw_point



class BlUser(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)

        self.icon = 'CON_ARMATURE'
    
        if self.buffer:
            self.load(self.buffer, self.pointer)
    def construct(self, name):
        return presence.User()
    
    def load(self, data, target):      
        target.name = data['name']
        target.location = data['location']
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


    def dump(self,pointer=None):
        data = utils.dump_anything.dump(pointer)
        data['location'] = pointer.location
        data['color'] = pointer.color
        return data


    def diff(self):
        for i,coord in enumerate(self.pointer.location):
            if coord != self.buffer['location'][i]:
                return True
        return False

bl_id = "users"
bl_class = presence.User
bl_rep_class = BlUser 

