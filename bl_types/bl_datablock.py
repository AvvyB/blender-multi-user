import bpy
import mathutils

from .. import utils
from ..libs.replication.replication.data import ReplicatedDatablock


class BlDatablock(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.pointer and hasattr(self.pointer, 'uuid'):
            self.pointer.uuid = self.uuid

    def bl_diff(self):
        """Generic datablock diff"""
        return self.pointer.name != self.buffer['name']
