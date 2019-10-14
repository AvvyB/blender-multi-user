import bpy
import mathutils

from .. import utils
from ..libs.replication.replication.data import ReplicatedDatablock
from ..libs.replication.replication.constants import UP


class BlDatablock(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pointer = kwargs.get('pointer', None)
        
        # TODO: use is_library_indirect
        self.is_library = (pointer and hasattr(pointer, 'library') and
                           pointer.library) or \
                           (self.data and 'library' in  self.data)

        if self.is_library:
            self.load = self.load_library
            self.dump = self.dump_library
            self.diff = self.diff_library
            self.resolve_dependencies = self.resolve_dependencies_library
            
        if self.pointer and hasattr(self.pointer, 'uuid'):
            self.pointer.uuid = self.uuid

    def library_apply(self):
        """Apply stored data
        """
        # UP in case we want to reset our pointer data
        self.state = UP

    def bl_diff(self):
        """Generic datablock diff"""
        return self.pointer.name != self.data['name']

    def construct_library(self, data):
        return None

    def load_library(self, data, target):
        pass

    def dump_library(self, pointer=None):
        return utils.dump_datablock(pointer, 1)

    def diff_library(self):
        return False

    def resolve_dependencies_library(self):
        return [self.pointer.library]

    def resolve_dependencies(self):
        dependencies = []

        if hasattr(self.pointer,'animation_data') and self.pointer.animation_data:
            dependencies.append(self.pointer.animation_data.action)
        
        return dependencies

    def is_valid(self):
        raise NotImplementedError