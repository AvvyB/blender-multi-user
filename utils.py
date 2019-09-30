import json
import logging
import os
import random
import string
import sys
from uuid import uuid4

import bpy
import mathutils

from . import environment, presence
from .libs import dump_anything

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def get_datablock_users(datablock):
    users = []
    supported_types = bpy.context.window_manager.session.supported_datablock
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


def random_string_digits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


def clean_scene():
    for type_name in dir(bpy.data):
        try:
            type_collection = getattr(bpy.data, type_name)
            for item in type_collection:
                type_collection.remove(item)
        except:
            continue


def revers(d):
    l = []
    for i in d:
        l.append(i)

    return l[::-1]


def get_armature_edition_context(armature):

    override = {}
    # Set correct area
    for area in bpy.data.window_managers[0].windows[0].screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()
            override['area'] = area
            break

    # Set correct armature settings
    override['window'] = bpy.data.window_managers[0].windows[0]
    override['screen'] = bpy.data.window_managers[0].windows[0].screen
    override['mode'] = 'EDIT_ARMATURE'
    override['active_object'] = armature
    override['selected_objects'] = [armature]

    for o in bpy.data.objects:
        if o.data == armature:
            override['edit_object'] = o

            break

    return override


def get_selected_objects(scene):
    return [obj.name for obj in scene.objects if obj.select_get()]


def load_dict(src_dict, target):
    try:
        for item in src_dict:
            # attr =
            setattr(target, item, src_dict[item])

    except Exception as e:
        logger.error(e)
        pass


def dump_datablock(datablock, depth):
    if datablock:
        dumper = dump_anything.Dumper()
        dumper.type_subset = dumper.match_subset_all
        dumper.depth = depth

        datablock_type = datablock.bl_rna.name
        key = "{}/{}".format(datablock_type, datablock.name)
        data = dumper.dump(datablock)

        return data


def dump_datablock_attibutes(datablock=None, attributes=[], depth=1, dickt=None):
    if datablock:
        dumper = dump_anything.Dumper()
        dumper.type_subset = dumper.match_subset_all
        dumper.depth = depth

        datablock_type = datablock.bl_rna.name

        data = {}

        if dickt:
            data = dickt
        for attr in attributes:
            try:
                data[attr] = dumper.dump(getattr(datablock, attr))
            except:
                pass

        return data
