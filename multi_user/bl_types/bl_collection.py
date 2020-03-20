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

from .. import utils
from .bl_datablock import BlDatablock


class BlCollection(BlDatablock):
    bl_id = "collections"
    bl_icon = 'FILE_FOLDER'
    bl_class = bpy.types.Collection
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True

    def _construct(self, data):
        if self.is_library:
            with bpy.data.libraries.load(filepath=bpy.data.libraries[self.data['library']].filepath, link=True) as (sourceData, targetData):
                targetData.collections = [
                    name for name in sourceData.collections if name == self.data['name']]
            
            instance = bpy.data.collections[self.data['name']]
            instance.uuid = self.uuid
            
            return instance

        instance = bpy.data.collections.new(data["name"])
        instance.uuid = self.uuid
        return instance

    def load_implementation(self, data, target):
        # Load other meshes metadata
        # dump_anything.load(target, data)
        target.name = data["name"]
        
        # link objects
        for object in data["objects"]:
            object_ref = utils.find_from_attr('uuid', object, bpy.data.objects)
            if object_ref and object_ref.name not in target.objects.keys():
                target.objects.link(object_ref)

        for object in target.objects:
            if object.uuid not in data["objects"]:
                target.objects.unlink(object)

        # Link childrens
        for collection in data["children"]:
            collection_ref = utils.find_from_attr(
                'uuid', collection, bpy.data.collections)
            if collection_ref and collection_ref.name not in target.children.keys():
                target.children.link(collection_ref)

        for collection in target.children:
            if collection.uuid not in data["children"]:
                target.children.unlink(collection)

    def dump_implementation(self, data, pointer=None):
        assert(pointer)
        data = {}
        data['name'] = pointer.name

        # dump objects
        collection_objects = []
        for object in pointer.objects:
            if object not in collection_objects:
                collection_objects.append(object.uuid)

        data['objects'] = collection_objects

        # dump children collections
        collection_children = []
        for child in pointer.children:
            if child not in collection_children:
                collection_children.append(child.uuid)

        data['children'] = collection_children

        return data

    def resolve_deps_implementation(self):
        deps = []

        for child in self.pointer.children:
            deps.append(child)
        for object in self.pointer.objects:
            deps.append(object)

        return deps

