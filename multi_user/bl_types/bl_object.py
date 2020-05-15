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

from .dump_anything import Loader, Dumper
from .bl_datablock import BlDatablock
from ..libs.replication.replication.exception import ContextError


def load_pose(target_bone, data):
    target_bone.rotation_mode = data['rotation_mode']
    loader = Loader()
    loader.load(target_bone, data)


class BlObject(BlDatablock):
    bl_id = "objects"
    bl_class = bpy.types.Object
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
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
        if "data" not in data:
            pass
        elif data["data"] in bpy.data.meshes.keys():
            instance = bpy.data.meshes[data["data"]]
        elif data["data"] in bpy.data.lights.keys():
            instance = bpy.data.lights[data["data"]]
        elif data["data"] in bpy.data.cameras.keys():
            instance = bpy.data.cameras[data["data"]]
        elif data["data"] in bpy.data.curves.keys():
            instance = bpy.data.curves[data["data"]]
        elif data["data"] in bpy.data.metaballs.keys():
            instance = bpy.data.metaballs[data["data"]]
        elif data["data"] in bpy.data.armatures.keys():
            instance = bpy.data.armatures[data["data"]]
        elif data["data"] in bpy.data.grease_pencils.keys():
            instance = bpy.data.grease_pencils[data["data"]]
        elif data["data"] in bpy.data.curves.keys():
            instance = bpy.data.curves[data["data"]]
        elif data["data"] in bpy.data.lattices.keys():
            instance = bpy.data.lattices[data["data"]]
        elif data["data"] in bpy.data.speakers.keys():
            instance = bpy.data.speakers[data["data"]]
        elif data["data"] in bpy.data.lightprobes.keys():
            # Only supported since 2.83
            if bpy.app.version[1] >= 83:
                instance = bpy.data.lightprobes[data["data"]]
            else:
                logging.warning(
                    "Lightprobe replication only supported since 2.83. See https://developer.blender.org/D6396")
        instance = bpy.data.objects.new(data["name"], instance)
        instance.uuid = self.uuid

        return instance

    def _load_implementation(self, data, target):
        # Load transformation data
        loader = Loader()
        loader.load(target, data)

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

        # vertex groups
        if 'vertex_groups' in data:
            target.vertex_groups.clear()
            for vg in data['vertex_groups']:
                vertex_group = target.vertex_groups.new(name=vg['name'])
                point_attr =  'vertices' if 'vertices' in vg else 'points'
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

    def _dump_implementation(self, data, instance=None):
        assert(instance)
        
        child_data = getattr(instance, 'data', None)
        
        if child_data and hasattr(child_data, 'is_editmode') and child_data.is_editmode:
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
            "instance_collection",
            "instance_type",
            "location",
            "scale",
            'rotation_quaternion' if instance.rotation_mode == 'QUATERNION' else 'rotation_euler',
        ]

        data = dumper.dump(instance)

        if self.is_library:
            return data

        # MODIFIERS
        if hasattr(instance, 'modifiers'):
            dumper.include_filter = None
            dumper.depth = 2
            data["modifiers"] = {}
            for index, modifier in enumerate(instance.modifiers):
                data["modifiers"][modifier.name] = dumper.dump(modifier)

        # CONSTRAINTS
        # OBJECT
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
            points_attr = 'vertices' if isinstance(instance.data, bpy.types.Mesh) else 'points'
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

        return deps

