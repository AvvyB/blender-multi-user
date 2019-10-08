import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock
from jsondiff import diff


class BlObject(BlDatablock):
    def construct(self, data):
        pointer = None

        if self.is_library:
            with bpy.data.libraries.load(filepath=bpy.data.libraries[self.data['library']].filepath, link=True) as (sourceData, targetData):
                targetData.objects = [
                    name for name in sourceData.objects if name == self.data['name']]

            return targetData.objects[self.data['name']]

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

    def load(self, data, target):
        target.matrix_world = mathutils.Matrix(data["matrix_world"])

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

        if 'children' in data.keys():
            for child in data['children']:
                bpy.data.objects[child].parent = self.pointer

    def dump(self, pointer=None):
        assert(pointer)
        dumper = utils.dump_anything.Dumper()
        dumper.depth = 1
        dumper.include_filter = [
            "name",
            "matrix_world",
            "rotation_mode",
            "parent",
            "data",
            "children",
            "library"
        ]
        data = dumper.dump(pointer)

        if self.is_library:
            return data

        if hasattr(pointer, 'modifiers'):
            dumper.include_filter = None
            dumper.depth = 3
            data["modifiers"] = dumper.dump(pointer.modifiers)
        
        if len(pointer.children) > 0:
            childs = []
            for child in pointer.children:
                childs.append(child.name)
           
            data["children"] = childs
            # deps.extend(list(self.pointer.children))
        return data

    def resolve(self):
        assert(self.data)
        self.pointer = utils.find_from_attr('uuid', self.uuid, bpy.data.objects)
        # object_name = self.data['name']
        # try:
        #     self.pointer = bpy.data.objects[object_name]
        # except:
        #     pass

    def resolve_dependencies(self):
        deps = []

        # Avoid Empty case
        if self.pointer.data:
            deps.append(self.pointer.data)
        if len(self.pointer.children) > 0:
            deps.extend(list(self.pointer.children))

        if self.is_library:
            deps.append(self.pointer.library)

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
