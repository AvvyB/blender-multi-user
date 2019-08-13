import bpy
import mathutils

from .. import utils
from ..presence import User
from ..libs.replication.data import ReplicatedDatablock
from ..libs.debug import draw_point

class BlUser(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)

        self.icon = 'CON_ARMATURE'
    
        if self.buffer:
            self.load(self.buffer, self.pointer)
    def construct(self, name):
        return User()
    
    def load(self, data, target):      
        target.name = data['name']
        target.location = data['location']
        utils.dump_anything.load(target, data)
    
    def dump(self,pointer=None):
        data = utils.dump_anything.dump(pointer)
        data['location'] = pointer.location
        data['color'] = pointer.color
        return data


    def diff(self):
        for i,coord in enumerate(self.pointer.location):
            if coord != self.buffer['location'][i]:
                print("user location update")
                return True
        return False

bl_id = "users"
bl_class = User
bl_rep_class = BlUser 

