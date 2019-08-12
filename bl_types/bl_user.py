import bpy
import mathutils

from .. import utils
from ..presence import User
from ..libs.replication.data import ReplicatedDatablock

class BlUser(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)

        self.icon = 'CON_ARMATURE'

        #TODO: investigate on empty buffer...
        if self.buffer:
            self.load(self.buffer, self.pointer)
    
    def load(self, data, target):
        if target is None:
            target = User()
        
        target.name = data['name']
        
    
    def dump(self,pointer=None):
        return utils.dump_anything.dump(pointer)

    def diff(self):
        pass

bl_id = "user"
bl_class = User
bl_rep_class = BlUser 

