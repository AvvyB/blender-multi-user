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


import bpy
import mathutils
import logging

from .. import utils
from .bl_datablock import BlDatablock

logger = logging.getLogger(__name__)


def load_pose(target_bone, data):
    target_bone.rotation_mode = data['rotation_mode']

    utils.dump_anything.load(target_bone, data)


class BlObject(BlDatablock):
    bl_id = "objects"
    bl_class = bpy.types.Object
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'OBJECT_DATA'

    def _construct(self, data):
        pointer = None

        if self.is_library:
            with bpy.data.libraries.load(filepath=bpy.data.libraries[self.data['library']].filepath, link=True) as (sourceData, targetData):
                targetData.objects = [
                    name for name in sourceData.objects if name == self.data['name']]

            instance = bpy.data.objects[self.data['name']]
            instance.uuid = self.uuid
            return instance

        # Object specific constructor...
        if "data" not in data:
            pass
        elif data["data"] in bpy.data.meshes.keys():
            pointer = bpy.data.meshes[data["data"]]
        elif data["data"] in bpy.data.lights.keys():
            pointer = bpy.data.lights[data["data"]]
        elif data["data"] in bpy.data.cameras.keys():
            pointer = bpy.data.cameras[data["data"]]
        elif data["data"] in bpy.data.curves.keys():
            pointer = bpy.data.curves[data["data"]]
        elif data["data"] in bpy.data.metaballs.keys():
            pointer = bpy.data.metaballs[data["data"]]
        elif data["data"] in bpy.data.armatures.keys():
            pointer = bpy.data.armatures[data["data"]]
        elif data["data"] in bpy.data.grease_pencils.keys():
            pointer = bpy.data.grease_pencils[data["data"]]
        elif data["data"] in bpy.data.curves.keys():
            pointer = bpy.data.curves[data["data"]]
        elif data["data"] in bpy.data.lattices.keys():
            pointer = bpy.data.lattices[data["data"]]
        elif data["data"] in bpy.data.speakers.keys():
            pointer = bpy.data.speakers[data["data"]]
        elif data["data"] in bpy.data.lightprobes.keys():
            # Only supported since 2.83
            if bpy.app.version[1] >= 83:
                pointer = bpy.data.lightprobes[data["data"]]
            else:
                logger.warning(
                    "Lightprobe replication only supported since 2.83. See https://developer.blender.org/D6396")
        instance = bpy.data.objects.new(data["name"], pointer)
        instance.uuid = self.uuid

        return instance

    def load_implementation(self, data, target):
        # Load transformation data
        utils.dump_anything.load(target, data)

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

                utils.dump_anything.load(bg_target, bg_data)
                # target.pose.bone_groups.get

            # Bones
            for bone in data['pose']['bones']:
                target_bone = target.pose.bones.get(bone)
                bone_data = data['pose']['bones'].get(bone)

                if 'constraints' in bone_data.keys():
                    utils.dump_anything.load(target_bone, bone_data['constraints'])


                load_pose(target_bone, bone_data)

                if 'bone_index' in bone_data.keys():
                    target_bone.bone_group = target.pose.bone_group[bone_data['bone_group_index']]

        # vertex groups
        if 'vertex_groups' in data:
            target.vertex_groups.clear()
            for vg in data['vertex_groups']:
                vertex_group = target.vertex_groups.new(name=vg['name'])
                for vert in vg['vertices']:
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

                utils.dump_anything.load(
                    target.data.shape_keys.key_blocks[key_block], key_data)
                for vert in key_data['data']:
                    target.data.shape_keys.key_blocks[key_block].data[vert].co = key_data['data'][vert]['co']

            # Load relative key after all
            for key_block in data['shape_keys']['key_blocks']:
                reference = data['shape_keys']['key_blocks'][key_block]['relative_key']

                target.data.shape_keys.key_blocks[key_block].relative_key = target.data.shape_keys.key_blocks[reference]

    def dump_implementation(self, data, pointer=None):
        assert(pointer)
        dumper = utils.dump_anything.Dumper()
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
            "instance_collection",
            "instance_type",
            "location",
            "scale",
            'rotation_quaternion' if pointer.rotation_mode == 'QUATERNION' else 'rotation_euler',
        ]

        data = dumper.dump(pointer)

        if self.is_library:
            return data

        # MODIFIERS
        if hasattr(pointer, 'modifiers'):
            dumper.include_filter = None
            dumper.depth = 2
            data["modifiers"] = {}
            for index, modifier in enumerate(pointer.modifiers):
                data["modifiers"][modifier.name] = dumper.dump(modifier)

        # CONSTRAINTS
        # OBJECT
        if hasattr(pointer, 'constraints'):
            dumper.depth = 3
            data["constraints"] = dumper.dump(pointer.constraints)

        # POSE
        if hasattr(pointer, 'pose') and pointer.pose:
            # BONES
            bones = {}
            for bone in pointer.pose.bones:
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
            for group in pointer.pose.bone_groups:
                dumper.depth = 3
                dumper.include_filter = [
                    'name',
                    'color_set'
                ]
                bone_groups[group.name] = dumper.dump(group)
            data['pose']['bone_groups'] = bone_groups

        # CHILDS
        if len(pointer.children) > 0:
            childs = []
            for child in pointer.children:
                childs.append(child.name)

            data["children"] = childs

        # VERTEx GROUP
        if len(pointer.vertex_groups) > 0:
            vg_data = []
            for vg in pointer.vertex_groups:
                vg_idx = vg.index
                dumped_vg = {}
                dumped_vg['name'] = vg.name

                vertices = []

                for v in pointer.data.vertices:
                    for vg in v.groups:
                        if vg.group == vg_idx:
                            vertices.append({
                                'index': v.index,
                                'weight': vg.weight
                            })

                dumped_vg['vertices'] = vertices

                vg_data.append(dumped_vg)

            data['vertex_groups'] = vg_data

        #  SHAPE KEYS
        pointer_data = pointer.data
        if hasattr(pointer_data, 'shape_keys') and pointer_data.shape_keys:
            dumper = utils.dump_anything.Dumper()
            dumper.depth = 2
            dumper.include_filter = [
                'reference_key',
                'use_relative'
            ]
            data['shape_keys'] = dumper.dump(pointer_data.shape_keys)
            data['shape_keys']['reference_key'] = pointer_data.shape_keys.reference_key.name
            key_blocks = {}
            for key in pointer_data.shape_keys.key_blocks:
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

    def resolve_deps_implementation(self):
        deps = []
    
        # Avoid Empty case
        if self.pointer.data:
            deps.append(self.pointer.data)
        if len(self.pointer.children) > 0:
            deps.extend(list(self.pointer.children))

        if self.is_library:
            deps.append(self.pointer.library)

        if self.pointer.instance_type == 'COLLECTION':
            # TODO: uuid based
            deps.append(self.pointer.instance_collection)

        return deps

