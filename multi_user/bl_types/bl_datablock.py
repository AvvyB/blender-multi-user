import bpy
import mathutils

from .. import utils
from ..libs.replication.replication.data import ReplicatedDatablock
from ..libs.replication.replication.constants import UP


def dump_driver(driver):
    dumper = utils.dump_anything.Dumper()
    dumper.depth = 6
    data = dumper.dump(driver)

    return data


def load_driver(target_datablock, src_driver):
    drivers = target_datablock.animation_data.drivers
    src_driver_data = src_driver['driver']
    new_driver = drivers.new(src_driver['data_path'])

    # Settings
    new_driver.driver.type = src_driver_data['type']
    new_driver.driver.expression = src_driver_data['expression']
    utils.dump_anything.load(new_driver,  src_driver)

    # Variables
    for src_variable in src_driver_data['variables']:
        src_var_data = src_driver_data['variables'][src_variable]
        new_var = new_driver.driver.variables.new()
        new_var.name = src_var_data['name']
        new_var.type = src_var_data['type']

        for src_target in src_var_data['targets']:
            src_target_data = src_var_data['targets'][src_target]
            new_var.targets[src_target].id = utils.resolve_from_id(
                src_target_data['id'], src_target_data['id_type'])
            utils.dump_anything.load(
                new_var.targets[src_target],  src_target_data)

    # Fcurve
    new_fcurve = new_driver.keyframe_points
    for p in reversed(new_fcurve):
        new_fcurve.remove(p, fast=True)

    new_fcurve.add(len(src_driver['keyframe_points']))

    for index, src_point in enumerate(src_driver['keyframe_points']):
        new_point = new_fcurve[index]
        utils.dump_anything.load(
            new_point, src_driver['keyframe_points'][src_point])


class BlDatablock(ReplicatedDatablock):
    """BlDatablock

        bl_id :             blender internal storage identifier
        bl_class :          blender internal type
        bl_delay_refresh :  refresh rate in second for observers
        bl_delay_apply :    refresh rate in sec for apply
        bl_automatic_push : boolean
        bl_icon :           type icon (blender icon name) 
    """
    bl_id = "scenes"

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

    def resolve(self):
        self.pointer = utils.find_from_attr('uuid', self.uuid, bpy.data.scenes)

        if not self.pointer:
            self.pointer = getattr(bpy.data,self.bl_id).get(self.data['name'])
            print(self.data['name'])
            if self.pointer:
                setattr(self.pointer, 'uuid', self.uuid)
                

    def dump(self, pointer=None):
        data = {}
        if utils.has_action(pointer):
            dumper = utils.dump_anything.Dumper()
            dumper.include_filter = ['action']
            data['animation_data'] = dumper.dump(pointer.animation_data)

        if utils.has_driver(pointer):
            dumped_drivers = {'animation_data': {'drivers': []}}
            for driver in pointer.animation_data.drivers:
                dumped_drivers['animation_data']['drivers'].append(
                    dump_driver(driver))

            data.update(dumped_drivers)
        data.update(self.dump_implementation(data, pointer=pointer))

        return data

    def dump_implementation(self, data, target):
        raise NotImplementedError

    def load(self, data, target):
        # Load animation data
        if 'animation_data' in data.keys():
            if target.animation_data is None:
                target.animation_data_create()

            for d in target.animation_data.drivers:
                target.animation_data.drivers.remove(d)

            if 'drivers' in data['animation_data']:
                for driver in data['animation_data']['drivers']:
                    load_driver(target, driver)

            if 'action' in data['animation_data']:
                target.animation_data.action = bpy.data.actions[data['animation_data']['action']]

        self.load_implementation(data, target)

    def load_implementation(self, data, target):
        raise NotImplementedError

    def resolve_dependencies(self):
        dependencies = []

        if utils.has_action(self.pointer):
            dependencies.append(self.pointer.animation_data.action)

        return dependencies

    def is_valid(self):
        raise NotImplementedError
