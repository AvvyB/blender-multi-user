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

import bpy
import mathutils
from replication.exception import ContextError

from .bl_datablock import BlDatablock, get_datablock_from_uuid
from .dump_anything import Dumper, Loader


def load_pose(target_bone, data):
    target_bone.rotation_mode = data['rotation_mode']
    loader = Loader()
    loader.load(target_bone, data)


def find_data_from_name(name=None):
    instance = None
    if not name:
        pass
    elif name in bpy.data.meshes.keys():
        instance = bpy.data.meshes[name]
    elif name in bpy.data.lights.keys():
        instance = bpy.data.lights[name]
    elif name in bpy.data.cameras.keys():
        instance = bpy.data.cameras[name]
    elif name in bpy.data.curves.keys():
        instance = bpy.data.curves[name]
    elif name in bpy.data.metaballs.keys():
        instance = bpy.data.metaballs[name]
    elif name in bpy.data.armatures.keys():
        instance = bpy.data.armatures[name]
    elif name in bpy.data.grease_pencils.keys():
        instance = bpy.data.grease_pencils[name]
    elif name in bpy.data.curves.keys():
        instance = bpy.data.curves[name]
    elif name in bpy.data.lattices.keys():
        instance = bpy.data.lattices[name]
    elif name in bpy.data.speakers.keys():
        instance = bpy.data.speakers[name]
    elif name in bpy.data.lightprobes.keys():
        # Only supported since 2.83
        if bpy.app.version[1] >= 83:
            instance = bpy.data.lightprobes[name]
        else:
            logging.warning(
                "Lightprobe replication only supported since 2.83. See https://developer.blender.org/D6396")
    return instance


def load_data(object, name):
    logging.info("loading data")
    pass


def _is_editmode(object: bpy.types.Object) -> bool:
    child_data = getattr(object, 'data', None)
    return (child_data and
            hasattr(child_data, 'is_editmode') and
            child_data.is_editmode)


def find_textures_dependencies(collection):
    """ Check collection
    """
    textures = []
    for item in collection:
        for attr in dir(item):
            inst = getattr(item, attr)
            if issubclass(type(inst), bpy.types.Texture) and inst is not None:
                textures.append(inst)

    return textures


class BlObject(BlDatablock):
    bl_id = "objects"
    bl_class = bpy.types.Object
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = False
    bl_icon = 'OBJECT_DATA'

    def _construct(self, data):
        instance = None

        if self.is_library:
            with bpy.data.libraries.load(filepath=bpy.data.libraries[self.data['library']].filepath, link=True) as (sourceData, targetData):
                targetData.objects = [
                    name for name in sourceData.objects if name == self.data['name']]

            instance = bpy.data.objects[self.data['name']]
            instance.uuid = self.uuid
            return instance

        # TODO: refactoring
        object_name = data.get("name")
        data_uuid = data.get("data_uuid")
        data_id = data.get("data")

        object_data = get_datablock_from_uuid(
            data_uuid,
            find_data_from_name(data_id),
            ignore=['images'])  # TODO: use resolve_from_id
        instance = bpy.data.objects.new(object_name, object_data)
        instance.uuid = self.uuid

        return instance

    def _load_implementation(self, data, target):
        loader = Loader()

        data_uuid = data.get("data_uuid")
        data_id = data.get("data")

        if target.data and (target.data.name != data_id):
            target.data = get_datablock_from_uuid(
                data_uuid, find_data_from_name(data_id), ignore=['images'])

        # vertex groups
        if 'vertex_groups' in data:
            target.vertex_groups.clear()
            for vg in data['vertex_groups']:
                vertex_group = target.vertex_groups.new(name=vg['name'])
                point_attr = 'vertices' if 'vertices' in vg else 'points'
                for vert in vg[point_attr]:
                    vertex_group.add(
                        [vert['index']], vert['weight'], 'REPLACE')

        # SHAPE KEYS
        if 'shape_keys' in data:
            target.shape_key_clear()

            object_data = target.data

            # Create keys and load vertices coords
            for key_block in data['shape_keys']['key_blocks']:
                key_data = data['shape_keys']['key_blocks'][key_block]
                target.shape_key_add(name=key_block)

                loader.load(
                    target.data.shape_keys.key_blocks[key_block], key_data)
                for vert in key_data['data']:
                    target.data.shape_keys.key_blocks[key_block].data[vert].co = key_data['data'][vert]['co']

            # Load relative key after all
            for key_block in data['shape_keys']['key_blocks']:
                reference = data['shape_keys']['key_blocks'][key_block]['relative_key']

                target.data.shape_keys.key_blocks[key_block].relative_key = target.data.shape_keys.key_blocks[reference]

        # Load transformation data
        loader.load(target, data)

        loader.load(target.display, data['display'])

        # Pose
        if 'pose' in data:
            if not target.pose:
                raise Exception('No pose data yet (Fixed in a near futur)')
            # Bone groups
            for bg_name in data['pose']['bone_groups']:
                bg_data = data['pose']['bone_groups'].get(bg_name)
                bg_target = target.pose.bone_groups.get(bg_name)

                if not bg_target:
                    bg_target = target.pose.bone_groups.new(name=bg_name)

                loader.load(bg_target, bg_data)
                # target.pose.bone_groups.get

            # Bones
            for bone in data['pose']['bones']:
                target_bone = target.pose.bones.get(bone)
                bone_data = data['pose']['bones'].get(bone)

                if 'constraints' in bone_data.keys():
                    loader.load(target_bone, bone_data['constraints'])

                load_pose(target_bone, bone_data)

                if 'bone_index' in bone_data.keys():
                    target_bone.bone_group = target.pose.bone_group[bone_data['bone_group_index']]

        # TODO: find another way...
        if target.empty_display_type == "IMAGE":
            img_uuid = data.get('data_uuid')
            if target.data is None and img_uuid:
                target.data = get_datablock_from_uuid(img_uuid, None)

    def _dump_implementation(self, data, instance=None):
        assert(instance)

        if _is_editmode(instance):
            if self.preferences.sync_flags.sync_during_editmode:
                instance.update_from_editmode()
            else:
                raise ContextError("Object is in edit-mode.")

        dumper = Dumper()
        dumper.depth = 1
        dumper.include_filter = [
            "name",
            "rotation_mode",
            "parent",
            "data",
            "children",
            "library",
            "empty_display_type",
            "empty_display_size",
            "empty_image_offset",
            "empty_image_depth",
            "empty_image_side",
            "show_empty_image_orthographic",
            "show_empty_image_perspective",
            "show_empty_image_only_axis_aligned",
            "use_empty_image_alpha",
            "color",
            "instance_collection",
            "instance_type",
            "location",
            "scale",
            'lock_location',
            'lock_rotation',
            'lock_scale',
            'hide_render',
            'display_type',
            'display_bounds_type',
            'show_bounds',
            'show_name',
            'show_axis',
            'show_wire',
            'show_all_edges',
            'show_texture_space',
            'show_in_front',
            'type',
            'rotation_quaternion' if instance.rotation_mode == 'QUATERNION' else 'rotation_euler',
        ]

        data = dumper.dump(instance)

        dumper.include_filter = [
            'show_shadows',
        ]
        data['display'] = dumper.dump(instance.display)

        data['data_uuid'] = getattr(instance.data, 'uuid', None)
        if self.is_library:
            return data

        # MODIFIERS
        if hasattr(instance, 'modifiers'):
            dumper.include_filter = None
            dumper.depth = 1
            data["modifiers"] = {}
            for index, modifier in enumerate(instance.modifiers):
                data["modifiers"][modifier.name] = dumper.dump(modifier)

        # CONSTRAINTS
        if hasattr(instance, 'constraints'):
            dumper.depth = 3
            data["constraints"] = dumper.dump(instance.constraints)

        # POSE
        if hasattr(instance, 'pose') and instance.pose:
            # BONES
            bones = {}
            for bone in instance.pose.bones:
                bones[bone.name] = {}
                dumper.depth = 1
                rotation = 'rotation_quaternion' if bone.rotation_mode == 'QUATERNION' else 'rotation_euler'
                group_index = 'bone_group_index' if bone.bone_group else None
                dumper.include_filter = [
                    'rotation_mode',
                    'location',
                    'scale',
                    'custom_shape',
                    'use_custom_shape_bone_size',
                    'custom_shape_scale',
                    group_index,
                    rotation
                ]
                bones[bone.name] = dumper.dump(bone)

                dumper.include_filter = []
                dumper.depth = 3
                bones[bone.name]["constraints"] = dumper.dump(bone.constraints)

            data['pose'] = {'bones': bones}

            # GROUPS
            bone_groups = {}
            for group in instance.pose.bone_groups:
                dumper.depth = 3
                dumper.include_filter = [
                    'name',
                    'color_set'
                ]
                bone_groups[group.name] = dumper.dump(group)
            data['pose']['bone_groups'] = bone_groups

        # CHILDS
        if len(instance.children) > 0:
            childs = []
            for child in instance.children:
                childs.append(child.name)

            data["children"] = childs

        # VERTEx GROUP
        if len(instance.vertex_groups) > 0:
            points_attr = 'vertices' if isinstance(
                instance.data, bpy.types.Mesh) else 'points'
            vg_data = []
            for vg in instance.vertex_groups:
                vg_idx = vg.index
                dumped_vg = {}
                dumped_vg['name'] = vg.name

                vertices = []

                for i, v in enumerate(getattr(instance.data, points_attr)):
                    for vg in v.groups:
                        if vg.group == vg_idx:
                            vertices.append({
                                'index': i,
                                'weight': vg.weight
                            })

                dumped_vg['vertices'] = vertices

                vg_data.append(dumped_vg)

            data['vertex_groups'] = vg_data

        #  SHAPE KEYS
        object_data = instance.data
        if hasattr(object_data, 'shape_keys') and object_data.shape_keys:
            dumper = Dumper()
            dumper.depth = 2
            dumper.include_filter = [
                'reference_key',
                'use_relative'
            ]
            data['shape_keys'] = dumper.dump(object_data.shape_keys)
            data['shape_keys']['reference_key'] = object_data.shape_keys.reference_key.name
            key_blocks = {}
            for key in object_data.shape_keys.key_blocks:
                dumper.depth = 3
                dumper.include_filter = [
                    'name',
                    'data',
                    'mute',
                    'value',
                    'slider_min',
                    'slider_max',
                    'data',
                    'co'
                ]
                key_blocks[key.name] = dumper.dump(key)
                key_blocks[key.name]['relative_key'] = key.relative_key.name
            data['shape_keys']['key_blocks'] = key_blocks

        return data

    def _resolve_deps_implementation(self):
        deps = []

        # Avoid Empty case
        if self.instance.data:
            deps.append(self.instance.data)
        if len(self.instance.children) > 0:
            deps.extend(list(self.instance.children))

        if self.is_library:
            deps.append(self.instance.library)

        if self.instance.instance_type == 'COLLECTION':
            # TODO: uuid based
            deps.append(self.instance.instance_collection)

        if self.instance.modifiers:
            deps.extend(find_textures_dependencies(self.instance.modifiers))

        return deps
