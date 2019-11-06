import bpy
import mathutils

from .. import utils
from ..libs.replication.replication.data import ReplicatedDatablock
from ..libs.replication.replication.constants import UP

def has_animation(target):
    return (hasattr(target, 'animation_data') \
                and target.animation_data \
                and target.animation_data.action)

class BlDatablock(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pointer = kwargs.get('pointer', None)

        # TODO: use is_library_indirect
        self.is_library = (pointer and hasattr(pointer, 'library') and
                           pointer.library) or \
            (self.data and 'library' in self.data)

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

    def dump(self, pointer=None):
        data = {}
        if has_animation(pointer):
            dumper = utils.dump_anything.Dumper()
            dumper.include_filter = ['action']
            data['animation_data'] = dumper.dump(pointer.animation_data)
            
        data.update(self.dump_implementation(data, pointer=pointer))

        return data        

    def dump_implementation(self, data, target):
        raise NotImplementedError

    def load(self, data, target):
        # Load animation data
        if 'animation_data' in data.keys():
            if target.animation_data is None:
                target.animation_data_create()
            
            
            target.animation_data.action = bpy.data.actions[data['animation_data']['action']]

        self.load_implementation(data, target)

    def load_implementation(self, data, target):
        raise NotImplementedError

    def resolve_dependencies(self):
        dependencies = []

        if has_animation(self.pointer):
            dependencies.append(self.pointer.animation_data.action)

        return dependencies


    def is_valid(self):
        raise NotImplementedError
