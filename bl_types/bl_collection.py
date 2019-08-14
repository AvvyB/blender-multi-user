import bpy
import mathutils

from .. import utils
from ..libs.replication.data import ReplicatedDatablock


class BlCollection(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        self.icon = 'FILE_FOLDER'

        super().__init__(*args, **kwargs)
    
    def construct(self,data):
        return bpy.data.collections.new(data["name"])

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
                if bpy.data.collections.find(collection) == -1:
                    target.children.link(
                        bpy.data.collections[collection])

        for collection in target.children.keys():
            if collection not in data["children"]:
                target.collection.children.unlink(
                    bpy.data.collections[collection])

        utils.dump_anything.load(target, data)

    def dump(self, pointer=None):
        assert(pointer)
        return utils.dump_datablock(pointer, 4)

    def resolve(self):
        assert(self.buffer)      
        self.pointer = bpy.data.collections.get(self.buffer['name'])
    
    def diff(self):
        return (len(self.pointer.objects) != self.buffer['objects'] or 
                len(self.pointer.collection.children) != self.buffer['collection']['children'])

bl_id = "collections"
bl_class = bpy.types.Collection
bl_rep_class = BlCollection
bl_delay_refresh = 1
bl_delay_apply = 1