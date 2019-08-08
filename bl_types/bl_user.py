import bpy
import mathutils

from .. import utils
from ..presence import User
from ..libs.replication.data import ReplicatedDatablock

class BlUser(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        self.icon = 'CON_ARMATURE'

        super().__init__( *args, **kwargs)
    
    def load(self, data, target):
        if target is None:
            target = User()
        
        utils.dump_anything.load(target,data)
    
    def dump(self,pointer=None):
        return utils.dump_anything.dump(pointer)
    # def load(self, data, target):
    #    pass


    # def dump(self, pointer=None):
    #     pass
        

bl_id = "user"
bl_class = User
bl_rep_class = BlUser 

