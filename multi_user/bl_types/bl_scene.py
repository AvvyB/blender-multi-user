import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock

class BlScene(BlDatablock):
    def construct(self, data):
        instance = bpy.data.scenes.new(data["name"])
        instance.uuid = self.uuid
        return instance

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
        for collection in data["collection"]["children"]:
            if collection not in target.collection.children.keys():
                target.collection.children.link(
                    bpy.data.collections[collection])

        for collection in target.collection.children.keys():
            if collection not in data["collection"]["children"]:
                target.collection.children.unlink(
                    bpy.data.collections[collection])

        if 'world' in data.keys():
            target.world = bpy.data.worlds[data['world']]
        
        # Annotation
        if 'grease_pencil' in data.keys():
            target.grease_pencil = bpy.data.grease_pencils[data['grease_pencil']]

    def dump(self, pointer=None):
        assert(pointer)
        data = {}

        scene_dumper = utils.dump_anything.Dumper()
        scene_dumper.depth = 1
        scene_dumper.include_filter = ['name','world', 'id', 'camera', 'grease_pencil']
        data = scene_dumper.dump(pointer)

        scene_dumper.depth = 3
        scene_dumper.include_filter = ['children','objects','name']
        data['collection'] = scene_dumper.dump(pointer.collection)
            

        return data

    def resolve(self):
        scene_name = self.data['name']
        
        self.pointer = bpy.data.scenes.get(scene_name)
        # self.pointer = utils.find_from_attr('uuid', self.uuid, bpy.data.objects)

    def resolve_dependencies(self):
        deps = []

        # child collections
        for child in self.pointer.collection.children:
            deps.append(child)
        
        # childs objects
        for object in self.pointer.objects:
            deps.append(object)
        
        # world
        if self.pointer.world:
            deps.append(self.pointer.world)
        
        # annotations
        if self.pointer.grease_pencil:
            deps.append(self.pointer.grease_pencil)

        return deps
    
    def is_valid(self):
        return bpy.data.scenes.get(self.data['name'])
bl_id = "scenes"
bl_class = bpy.types.Scene
bl_rep_class = BlScene
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'SCENE_DATA'