import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock


class BlObject(BlDatablock):
    def construct(self, data):
        pointer = None

        if self.is_library:
            with bpy.data.libraries.load(filepath=bpy.data.libraries[self.buffer['library']].filepath, link=True) as (sourceData, targetData):
                targetData.objects  = [name for name in sourceData.objects if name ==  self.buffer['name']]
            
            return  targetData.objects[self.buffer['name']]

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
        elif data["data"] in bpy.data.armatures.keys():
            pointer = bpy.data.armatures[data["data"]]
        elif data["data"] in bpy.data.grease_pencils.keys():
            pointer = bpy.data.grease_pencils[data["data"]]
        elif data["data"] in bpy.data.curves.keys():
            pointer = bpy.data.curves[data["data"]]

        return bpy.data.objects.new(data["name"], pointer)

    def load(self, data, target):
        # Load other meshes metadata
        utils.dump_anything.load(target, data)

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

    def dump(self, pointer=None):
        assert(pointer)
        data = utils.dump_datablock(pointer, 1)
        
        if self.is_library:
            return data

        if hasattr(pointer, 'modifiers'):
            utils.dump_datablock_attibutes(
                pointer, ['modifiers'], 3, data)
        return data

    def resolve(self):
        assert(self.buffer)
        object_name = self.buffer['name']

        self.pointer = bpy.data.objects.get(object_name)

    def diff(self):
        return (self.bl_diff() or
                self.dump(pointer=self.pointer)['matrix_world'] != self.buffer['matrix_world'])

    def resolve_dependencies(self):
        deps = []
        # Avoid Empty case
        if self.pointer.data:
            deps.append(self.pointer.data)

        if self.is_library:
            deps.append(self.pointer.library)

        return deps


bl_id = "objects"
bl_class = bpy.types.Object
bl_rep_class = BlObject
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'OBJECT_DATA'