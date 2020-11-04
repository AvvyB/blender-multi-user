# ##### BEGIN GPL LICENSE BLOCK #####
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


import logging
from collections.abc import Iterable

import bpy
import mathutils
from replication.constants import DIFF_BINARY, DIFF_JSON, UP
from replication.data import ReplicatedDatablock

from .. import utils
from .dump_anything import Dumper, Loader


def has_action(target):
    """ Check if the target datablock has actions
    """
    return (hasattr(target, 'animation_data')
            and target.animation_data
            and target.animation_data.action)


def has_driver(target):
    """ Check if the target datablock is driven
    """
    return (hasattr(target, 'animation_data')
            and target.animation_data
            and target.animation_data.drivers)


def dump_driver(driver):
    dumper = Dumper()
    dumper.depth = 6
    data = dumper.dump(driver)

    return data


def load_driver(target_datablock, src_driver):
    loader = Loader()
    drivers = target_datablock.animation_data.drivers
    src_driver_data = src_driver['driver']
    new_driver = drivers.new(src_driver['data_path'])

    # Settings
    new_driver.driver.type = src_driver_data['type']
    new_driver.driver.expression = src_driver_data['expression']
    loader.load(new_driver,  src_driver)

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
            loader.load(
                new_var.targets[src_target],  src_target_data)

    # Fcurve
    new_fcurve = new_driver.keyframe_points
    for p in reversed(new_fcurve):
        new_fcurve.remove(p, fast=True)

    new_fcurve.add(len(src_driver['keyframe_points']))

    for index, src_point in enumerate(src_driver['keyframe_points']):
        new_point = new_fcurve[index]
        loader.load(new_point, src_driver['keyframe_points'][src_point])


def get_datablock_from_uuid(uuid, default, ignore=[]):
    if not uuid:
        return default
    for category in dir(bpy.data):
        root = getattr(bpy.data, category)
        if isinstance(root, Iterable) and category not in ignore:
            for item in root:
                if getattr(item, 'uuid', None) == uuid:
                    return item
    return default


class BlDatablock(ReplicatedDatablock):
    """BlDatablock

        bl_id :             blender internal storage identifier
        bl_class :          blender internal type
        bl_delay_refresh :  refresh rate in second for observers
        bl_delay_apply :    refresh rate in sec for apply
        bl_automatic_push : boolean
        bl_icon :           type icon (blender icon name) 
        bl_check_common:    enable check even in common rights
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        
        self.preferences = utils.get_preferences()

        # TODO: use is_library_indirect
        self.is_library = (instance and hasattr(instance, 'library') and
                           instance.library) or \
            (hasattr(self,'data') and self.data and 'library' in self.data)

        if instance and hasattr(instance, 'uuid'):
            instance.uuid = self.uuid

        self.diff_method = DIFF_BINARY

    def resolve(self):
        datablock_ref = None
        datablock_root = getattr(bpy.data, self.bl_id)
        datablock_ref = utils.find_from_attr('uuid', self.uuid, datablock_root)

        if not datablock_ref:
            try:
                datablock_ref = datablock_root[self.data['name']]
            except Exception:
                name = self.data.get('name')
                logging.debug(f"Constructing {name}")
                datablock_ref = self._construct(data=self.data)

            if datablock_ref:
                setattr(datablock_ref, 'uuid', self.uuid)

        self.instance = datablock_ref

    def remove_instance(self):
        """
        Remove instance from blender data
        """
        assert(self.instance)

        datablock_root = getattr(bpy.data, self.bl_id)
        datablock_root.remove(self.instance)

    def _dump(self, instance=None):
        dumper = Dumper()
        data = {}
        # Dump animation data
        if has_action(instance):
            dumper = Dumper()
            dumper.include_filter = ['action']
            data['animation_data'] = dumper.dump(instance.animation_data)

        if has_driver(instance):
            dumped_drivers = {'animation_data': {'drivers': []}}
            for driver in instance.animation_data.drivers:
                dumped_drivers['animation_data']['drivers'].append(
                    dump_driver(driver))

            data.update(dumped_drivers)

        if self.is_library:
            data.update(dumper.dump(instance))
        else:
            data.update(self._dump_implementation(data, instance=instance))

        return data

    def _dump_implementation(self, data, target):
        raise NotImplementedError

    def _load(self, data, target):
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

        if self.is_library:
            return
        else:
            self._load_implementation(data, target)

    def _load_implementation(self, data, target):
        raise NotImplementedError

    def resolve_deps(self):
        dependencies = []

        if has_action(self.instance):
            dependencies.append(self.instance.animation_data.action)

        if not self.is_library:
            dependencies.extend(self._resolve_deps_implementation())

        logging.debug(f"{self.instance} dependencies: {dependencies}")
        return dependencies

    def _resolve_deps_implementation(self):
        return []

    def is_valid(self):
        return getattr(bpy.data, self.bl_id).get(self.data['name'])
