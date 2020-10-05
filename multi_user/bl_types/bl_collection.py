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


def dump_collection_children(collection):
    collection_children = []
    for child in collection.children:
        if child not in collection_children:
            collection_children.append(child.uuid)
    return collection_children


def dump_collection_objects(collection):
    collection_objects = []
    for object in collection.objects:
        if object not in collection_objects:
            collection_objects.append(object.uuid)

    return collection_objects


def load_collection_objects(dumped_objects, collection):
    for object in dumped_objects:
        object_ref = utils.find_from_attr('uuid', object, bpy.data.objects)

        if object_ref is None:
            continue
        elif object_ref.name not in collection.objects.keys():
            collection.objects.link(object_ref)

    for object in collection.objects:
        if object.uuid not in dumped_objects:
            collection.objects.unlink(object)


def load_collection_childrens(dumped_childrens, collection):
    for child_collection in dumped_childrens:
        collection_ref = utils.find_from_attr(
            'uuid',
            child_collection,
            bpy.data.collections)

        if collection_ref is None:
            continue
        if collection_ref.name not in collection.children.keys():
            collection.children.link(collection_ref)

    for child_collection in collection.children:
        if child_collection.uuid not in dumped_childrens:
            collection.children.unlink(child_collection)


class BlCollection(BlDatablock):
    bl_id = "collections"
    bl_icon = 'FILE_FOLDER'
    bl_class = bpy.types.Collection
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = True
    
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
        loader.load(target, data)

        # Objects
        load_collection_objects(data['objects'], target)

        # Link childrens
        load_collection_childrens(data['children'], target)

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
        data['objects'] = dump_collection_objects(instance)

        # dump children collections
        data['children'] = dump_collection_children(instance)

        return data

    def _resolve_deps_implementation(self):
        deps = []

        for child in self.instance.children:
            deps.append(child)
        for object in self.instance.objects:
            deps.append(object)

        return deps
