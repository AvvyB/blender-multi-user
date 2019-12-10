import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock


def load_constraints(target, data):
    for local_constraint in target.constraints:
        if local_constraint.name not in data:
            target.constraints.remove(local_constraint)

    for constraint in data:
        target_constraint = target.constraints.get(constraint)

        if not target_constraint:
            target_constraint = target.constraints.new(
                data[constraint]['type'])

        utils.dump_anything.load(
            target_constraint, data[constraint])


class BlObject(BlDatablock):
    def construct(self, data):
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
            pass
            # bpy need to support correct lightprobe creation from python
            # pointer = bpy.data.lightprobes[data["data"]]

        instance = bpy.data.objects.new(data["name"], pointer)
        instance.uuid = self.uuid

        return instance

    def load_implementation(self, data, target):
        if "matrix_world" in data:
            target.matrix_world = mathutils.Matrix(data["matrix_world"])

        target.name = data["name"]
        # Load modifiers
        if hasattr(target, 'modifiers'):
            # TODO: smarter selective update 
            target.modifiers.clear()

            for modifier in data['modifiers']:
                target_modifier = target.modifiers.get(modifier)

                if not target_modifier:
                    target_modifier = target.modifiers.new(
                        data['modifiers'][modifier]['name'], data['modifiers'][modifier]['type'])

                utils.dump_anything.load(
                    target_modifier, data['modifiers'][modifier])

        # Load constraints
        # Object
        if hasattr(target, 'constraints') and 'constraints' in data:
            load_constraints(target, data['constraints'])

        # Pose bone
        if 'pose' in data:
            if not target.pose:
                raise Exception('No pose...')
            for bone in data['pose']['bones']:
                target_bone = target.pose.bones.get(bone)
                load_constraints(
                    target_bone, data['pose']['bones'][bone]['constraints'])

        # Load relations
        if 'children' in data.keys():
            for child in data['children']:
                bpy.data.objects[child].parent = self.pointer

        # Load empty representation
        target.empty_display_size = data['empty_display_size']
        target.empty_display_type = data['empty_display_type']

        # Instancing
        target.instance_type = data['instance_type']
        if data['instance_type'] == 'COLLECTION':
            target.instance_collection = bpy.data.collections[data['instance_collection']]

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
                
                utils.dump_anything.load(target.data.shape_keys.key_blocks[key_block],key_data)
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
            "instance_type"
        ]
        if not utils.has_action(pointer):
            dumper.include_filter.append('matrix_world')

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
                data["modifiers"][modifier.name]['m_index'] = index

        # CONSTRAINTS
        # OBJECT
        if hasattr(pointer, 'constraints'):
            dumper.depth = 3
            data["constraints"] = dumper.dump(pointer.constraints)

        # POSE BONES
        if hasattr(pointer, 'pose') and pointer.pose:
            dumper.depth = 3
            bones = {}
            for bone in pointer.pose.bones:
                bones[bone.name] = {}
                bones[bone.name]["constraints"] = dumper.dump(bone.constraints)

            data['pose'] = {'bones': bones}

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
                dumped_vg = {}
                dumped_vg['name'] = vg.name
                dumped_vg['vertices'] = [{'index': v.index, 'weight': v.groups[vg.index].weight}
                                         for v in pointer.data.vertices if vg.index in [vg.group for vg in v.groups]]

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

    def resolve(self):
        self.pointer = utils.find_from_attr(
            'uuid', self.uuid, bpy.data.objects)

    def resolve_dependencies(self):
        deps = super().resolve_dependencies()

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

    def is_valid(self):
        return bpy.data.objects.get(self.data['name'])


bl_id = "objects"
bl_class = bpy.types.Object
bl_rep_class = BlObject
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'OBJECT_DATA'
