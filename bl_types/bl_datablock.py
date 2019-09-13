import bpy
import mathutils

from .. import utils
from ..libs.replication.replication.data import ReplicatedDatablock
from ..libs.replication.replication.constants import UP


class BlDatablock(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pointer = kwargs.get('pointer', None)
        buffer = self.buffer

        # TODO: use is_library_indirect
        self.is_library = (pointer and hasattr(pointer, 'library') and
                           pointer.library) or \
            (buffer and 'library' in buffer)
        #     :
        if self.is_library:
            self.load = self.load_library
            self.dump = self.dump_library
            self.diff = self.diff_library
            
        # self.construct = self.construct_library
        # self.resolve_dependencies = self.resolve_dependencies_library
        # self.apply = self.library_apply

        if self.pointer and hasattr(self.pointer, 'uuid'):
            self.pointer.uuid = self.uuid

    def library_apply(self):
        """Apply stored data
        """
        # UP in case we want to reset our pointer data
        self.state = UP

    def bl_diff(self):
        """Generic datablock diff"""
        return self.pointer.name != self.buffer['name']

    def construct_library(self, data):
        with bpy.data.libraries.load(filepath=bpy.data.libraries[self.buffer['library']].filepath, link=True) as (sourceData, targetData):
            # targetData[self.name] = sourceData
            print("asd")
        return None

    def load_library(self, data, target):
        print("asdasdas")

    def dump_library(self, pointer=None):
        return utils.dump_datablock(pointer, 1)

    def diff_library(self):
        return False

    def resolve_dependencies_library(self):
        return [self.pointer.library]
