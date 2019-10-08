import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock


class BlCollection(BlDatablock):
    def construct(self,data):
        instance = bpy.data.collections.new(data["name"])
        instance.uuid = self.uuid
        return instance

    def load(self, data, target):
        # Load other meshes metadata
        # dump_anything.load(target, data)
 
        # link objects
        for object in data["objects"]:
            if object not in target.objects.keys():
                target.objects.link(bpy.data.objects[object])

        for object in target.objects.keys():
            if object not in data["objects"]:
                target.objects.unlink(bpy.data.objects[object])

        # Link childrens
        for collection in data["children"]:
            if collection not in target.children.keys():
                # if bpy.data.collections.find(collection) == -1:
                target.children.link(
                    bpy.data.collections[collection])

        for collection in target.children.keys():
            if collection not in data["children"]:
                target.collection.children.unlink(
                    bpy.data.collections[collection])

        utils.dump_anything.load(target, data)

    def dump(self, pointer=None):
        assert(pointer)
        
        dumper = utils.dump_anything.Dumper()
        dumper.depth = 2
        dumper.include_filter = ['name','objects', 'children', 'uuid']

        return dumper.dump(pointer)

    def resolve(self):
        assert(self.data)      
        # self.pointer = bpy.data.collections.get(self.data['name'])
        self.pointer = utils.find_from_attr('uuid', self.uuid, bpy.data.collections)

    def resolve_dependencies(self):
        deps = []
        
        for child in self.pointer.children:
            deps.append(child)
        for object in self.pointer.objects:
            deps.append(object)
        
        return deps

    def is_valid(self):
        return bpy.data.collections.get(self.data['name'])
        
bl_id = "collections"
bl_icon = 'FILE_FOLDER'
bl_class = bpy.types.Collection
bl_rep_class = BlCollection
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True