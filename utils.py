import logging
import sys
from uuid import uuid4
import json
import os
import string
import random

import bpy
import mathutils

from . import presence, environment
from .libs import dump_anything

# TODO: replace hardcoded values...
BPY_TYPES = {'Image': 'images', 'Texture': 'textures', 'Material': 'materials', 'GreasePencil': 'grease_pencils', 'Curve': 'curves', 'Collection': 'collections', 'Mesh': 'meshes', 'Object': 'objects',
             'Scene': 'scenes', 'Light': 'lights', 'SunLight': 'lights', 'SpotLight': 'lights', 'AreaLight': 'lights', 'PointLight': 'lights', 'Camera': 'cameras', 'Action': 'actions', 'Armature': 'armatures'}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# UTILITY FUNCTIONS
def random_string_digits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


def refresh_window():
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

def clean_scene():
    for datablock in BPY_TYPES:
        datablock_ref = getattr(bpy.data,  BPY_TYPES[datablock])
        for item in datablock_ref:
            try:
                datablock_ref.remove(item)
            # Catch last scene remove
            except RuntimeError:
                pass


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
    selected_objects = []
    for obj in scene.objects:
        if obj.select_get():
            selected_objects.append(obj.name)

    return selected_objects

def load_dict(src_dict, target):
    try:
        for item in src_dict:
            # attr =
            setattr(target, item, src_dict[item])

    except Exception as e:
        logger.error(e)
        pass

def resolve_bpy_path(path):
    """
    Get bpy property value from path
    """
    item = None

    try:
        path = path.split('/')
        item = getattr(bpy.data, BPY_TYPES[path[0]])[path[1]]

    except:
        pass

    return item


def load_client(client=None, data=None):
    C = bpy.context
    D = bpy.data
    net_settings = C.window_manager.session

    if client and data:
        if net_settings.enable_presence:
            draw.renderer.draw_client(data)
            draw.renderer.draw_client_selected_objects(data)


def load_armature(target=None, data=None, create=False):
    file = "cache_{}.json".format(data['name'])
    context = bpy.context

    if not target:
        target = bpy.data.armatures.new(data['name'])

        dump_anything.load(target, data)

        with open(file, 'w') as fp:
            json.dump(data, fp)
            fp.close()

        target.id = data['id']
    else:
        # Construct a correct execution context
        file = "cache_{}.json".format(target.name)

        with open(file, 'r') as fp:
            data = json.load(fp)

            if data:
                ob = None
                for o in bpy.data.objects:
                    if o.data == target:
                        ob = o
                if ob:
                    bpy.context.view_layer.objects.active = ob
                    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                    for eb in data['edit_bones']:
                        if eb in target.edit_bones.keys():
                            # Update the bone
                            pass
                        else:
                            # Add new edit bone and load it

                            target_new_b = target.edit_bones.new[eb]
                            dump_anything.load(target_new_b, data['bones'][eb])

                        logger.debug(eb)

                    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            fp.close()
            import os
            os.remove(file)

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
        key = "{}/{}".format(datablock_type, datablock.name)

        data = {}

        if dickt:
            data = dickt
        for attr in attributes:
            try:
                data[attr] = dumper.dump(getattr(datablock, attr))
            except:
                pass

        return data




def init_client(key=None):
    client_dict = {}

    C = bpy.context
    Net = C.window_manager.session
    client_dict['uuid'] = str(uuid4())
    client_dict['location'] = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
    client_dict['color'] = [Net.client_color.r,
                            Net.client_color.g, Net.client_color.b, 1]

    client_dict['active_objects'] = get_selected_objects(C.view_layer)

    return client_dict
