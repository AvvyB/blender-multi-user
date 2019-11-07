import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock


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

        instance =  bpy.data.objects.new(data["name"], pointer)
        instance.uuid = self.uuid
        
        return instance

    def load_implementation(self, data, target):
        if "matrix_world" in data:
            target.matrix_world = mathutils.Matrix(data["matrix_world"])

        # vertex groups
        if 'vertex_groups' in data:
            target.vertex_groups.clear()
            for vg in data['vertex_groups']:
                vertex_group = target.vertex_groups.new(name=vg['name'])
                # TODO: assign vertex
                for vert in vg['vertices']:
                    vertex_group.add([vert['index']],vert['weight'],'REPLACE')
        
        target.name = data["name"]
        # Load modifiers
        if hasattr(target, 'modifiers'):
            for local_modifier in target.modifiers:
                if local_modifier.name not in data['modifiers']:
                    target.modifiers.remove(local_modifier)
            for modifier in data['modifiers']:
                target_modifier = target.modifiers.get(modifier)

                if not target_modifier:
                    target_modifier = target.modifiers.new(
                        data['modifiers'][modifier]['name'], data['modifiers'][modifier]['type'])

                utils.dump_anything.load(
                    target_modifier, data['modifiers'][modifier])
        
        # Load constraints
        if hasattr(target, 'constraints'):
            for local_constraint in target.constraints:
                if local_constraint.name not in data['modifiers']:
                    target.modifiers.remove(local_constraint)

            for constraint in data['constraints']:
                target_constraint = target.constraints.get(modifier)

                if not target_constraint:
                    target_constraint = target.constraints.new(data['constraints'][constraint]['type'])

                utils.dump_anything.load(
                    target_constraint, data['constraints'][constraint])

        # Load relations
        if 'children' in data.keys():
            for child in data['children']:
                bpy.data.objects[child].parent = self.pointer

        # Load empty representation
        target.empty_display_size = data['empty_display_size']
        target.empty_display_type = data['empty_display_type']

        # Instancing
        target.instance_type =  data['instance_type']
        if data['instance_type'] == 'COLLECTION':
            target.instance_collection = bpy.data.collections[data['instance_collection']]

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
        if not pointer.animation_data:
            dumper.include_filter.append('matrix_world')

        data = dumper.dump(pointer)

        if self.is_library:
            return data

        # MODIFIERS
        if hasattr(pointer, 'modifiers'):
            dumper.include_filter = None
            dumper.depth = 3
            data["modifiers"] = dumper.dump(pointer.modifiers)
        
        # CONSTRAINTS
        if hasattr(pointer, 'constraints'):
            dumper.include_filter = None
            dumper.depth = 3
            data["constraints"] = dumper.dump(pointer.constraints)

        # CHILDS
        if len(pointer.children) > 0:
            childs = []
            for child in pointer.children:
                childs.append(child.name)
           
            data["children"] = childs

        # VERTEx GROUP
        if len(pointer.vertex_groups)>0:
            vg_data = []
            for vg in pointer.vertex_groups:
                dumped_vg = {}
                dumped_vg['name'] = vg.name
                dumped_vg['vertices'] = [ {'index':v.index,'weight':v.groups[vg.index].weight} for v in pointer.data.vertices if vg.index in [ vg.group for vg in v.groups ] ]
                
                vg_data.append(dumped_vg)


            data['vertex_groups'] = vg_data
        return data

    def resolve(self):
        self.pointer = utils.find_from_attr('uuid', self.uuid, bpy.data.objects)

    def resolve_dependencies(self):
        deps = super().resolve_dependencies()

        # Avoid Empty case
        if self.pointer.data:
            deps.append(self.pointer.data)
        if len(self.pointer.children) > 0:
            deps.extend(list(self.pointer.children))

        if self.is_library:
            deps.append(self.pointer.library)

        if hasattr(self.pointer, 'modifiers'):
            for mod in self.pointer.modifiers:
                attributes = dir(mod)
                for attr in attributes:
                    attr_ref = getattr(mod, attr)
                    if attr_ref and isinstance(attr_ref, bpy.types.Object):
                        deps.append(attr_ref)

        if self.pointer.instance_type == 'COLLECTION':
            #TODO: uuid based
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
