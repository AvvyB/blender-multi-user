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
from .dump_anything import Loader, Dumper

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
            
            return instance

        instance = bpy.data.collections.new(data["name"])
        return instance

    def _load_implementation(self, data, target):
        loader = Loader()
        loader.load(target,data)

        # Load other meshes metadata
        # target.name = data["name"]
        
        # Objects
        for object in data["objects"]:
            object_ref = bpy.data.objects.get(object)

            if object_ref is None:
                continue

            if object not in target.objects.keys(): 
                target.objects.link(object_ref)

        for object in target.objects:
            if object.name not in data["objects"]:
                target.objects.unlink(object)

        # Link childrens
        for collection in data["children"]:
            collection_ref = bpy.data.collections.get(collection)

            if collection_ref is None:
                continue
            if collection_ref.name not in target.children.keys():
                target.children.link(collection_ref)

        for collection in target.children:
            if collection.name not in data["children"]:
                target.children.unlink(collection)

    def _dump_implementation(self, data, instance=None):
        assert(instance)

        dumper = Dumper()
        dumper.depth = 1
        dumper.include_filter = [
            "name",
            "instance_offset"
        ]
        data = dumper.dump(instance)

        # dump objects
        collection_objects = []
        for object in instance.objects:
            if object not in collection_objects:
                collection_objects.append(object.name)

        data['objects'] = collection_objects

        # dump children collections
        collection_children = []
        for child in instance.children:
            if child not in collection_children:
                collection_children.append(child.name)

        data['children'] = collection_children

        return data

    def _resolve_deps_implementation(self):
        deps = []

        for child in self.instance.children:
            deps.append(child)
        for object in self.instance.objects:
            deps.append(object)

        return deps
