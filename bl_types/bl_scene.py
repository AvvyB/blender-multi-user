import bpy
import mathutils
from jsondiff import diff

from .. import utils
from .bl_datablock import BlDatablock

class BlScene(BlDatablock):
    def construct(self, data):
        return bpy.data.scenes.new(data["name"])

    def load(self, data, target):
        target = self.pointer
        # Load other meshes metadata
        utils.dump_anything.load(target, data)

        # Load master collection
        for object in data["collection"]["objects"]:
            if object not in target.collection.objects.keys():
                target.collection.objects.link(bpy.data.objects[object])

        for object in target.collection.objects.keys():
            if object not in data["collection"]["objects"]:
                target.collection.objects.unlink(bpy.data.objects[object])

        # load collections
        # TODO: Recursive link
        for collection in data["collection"]["children"]:
            if collection not in target.collection.children.keys():
                target.collection.children.link(
                    bpy.data.collections[collection])

        for collection in target.collection.children.keys():
            if collection not in data["collection"]["children"]:
                target.collection.children.unlink(
                    bpy.data.collections[collection])

    def dump(self, pointer=None):
        assert(pointer)
        
        data = utils.dump_datablock_attibutes(
            pointer, ['name', 'collection', 'id', 'camera', 'grease_pencil'], 2)
        utils.dump_datablock_attibutes(
            pointer, ['collection'], 4, data)

        return data

    def resolve(self):
        assert(self.buffer)
        scene_name = self.buffer['name']
        
        self.pointer = bpy.data.scenes.get(scene_name)
    
    def diff(self):
        return (self.bl_diff() or
                len(self.pointer.collection.objects) != len(self.buffer['collection']['objects']) or 
                len(self.pointer.collection.children) != len(self.buffer['collection']['children']))

    def resolve_dependencies(self):
        deps = []
        
        for child in self.pointer.collection.children:
            deps.append(child)
        for object in self.pointer.objects:
            deps.append(object)
        
        return deps
        
bl_id = "scenes"
bl_class = bpy.types.Scene
bl_rep_class = BlScene
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'SCENE_DATA'