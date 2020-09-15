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


import json
import logging
import os
import sys
import time
from uuid import uuid4
from collections.abc import Iterable

import bpy
import mathutils

from . import environment, presence


def find_from_attr(attr_name, attr_value, list):
    for item in list:
        if getattr(item, attr_name, None) == attr_value:
            return item
    return None


def get_datablock_users(datablock):
    users = []
    supported_types = get_preferences().supported_datablocks
    if hasattr(datablock, 'users_collection') and datablock.users_collection:
        users.extend(list(datablock.users_collection))
    if hasattr(datablock, 'users_scene') and datablock.users_scene:
        users.extend(list(datablock.users_scene))
    if hasattr(datablock, 'users_group') and datablock.users_scene:
        users.extend(list(datablock.users_scene))
    for datatype in supported_types:
        if datatype.bl_name != 'users':
            root = getattr(bpy.data, datatype.bl_name)
            for item in root:
                if hasattr(item, 'data') and datablock == item.data or \
                        datatype.bl_name != 'collections' and hasattr(item, 'children') and datablock in item.children:
                    users.append(item)
    return users


def clean_scene():
    for type_name in dir(bpy.data):
        try:
            type_collection = getattr(bpy.data, type_name)
            for item in type_collection:
                type_collection.remove(item)
        except:
            continue


def get_selected_objects(scene, active_view_layer):
    return [obj.uuid for obj in scene.objects if obj.select_get(view_layer=active_view_layer)]


def resolve_from_id(id, optionnal_type=None):
    for category in dir(bpy.data):
        root = getattr(bpy.data, category)
        if isinstance(root, Iterable):
            if id in root and ((optionnal_type is None) or (optionnal_type.lower() in root[id].__class__.__name__.lower())):
                return root[id]
    return None


def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences


def current_milli_time():
    return int(round(time.time() * 1000))


def get_expanded_icon(prop: bpy.types.BoolProperty) -> str:
    if prop:
        return 'DISCLOSURE_TRI_DOWN'
    else:
        return 'DISCLOSURE_TRI_RIGHT'
