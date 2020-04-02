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

from .dump_anything import Loader, Dumper
from .bl_datablock import BlDatablock

class BlScene(BlDatablock):
    bl_id = "scenes"
    bl_class = bpy.types.Scene
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'SCENE_DATA'

    def _construct(self, data):
        instance = bpy.data.scenes.new(data["name"])
        instance.uuid = self.uuid
        return instance

    def _load_implementation(self, data, target):
        target = self.pointer
        # Load other meshes metadata
        loader = Loader()
        loader.load(target, data)

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

        if 'eevee' in data.keys():
            loader.load(target.eevee, data['eevee'])
        
        if 'cycles' in data.keys():
            loader.load(target.eevee, data['cycles'])

        if 'view_settings' in data.keys():
            loader.load(target.view_settings, data['view_settings'])
            target.view_settings.curve_mapping.update()

    def _dump_implementation(self, data, pointer=None):
        assert(pointer)
        data = {}

        scene_dumper = Dumper()
        scene_dumper.depth = 1
        scene_dumper.include_filter = [
            'name',
            'world',
            'id',
            'camera',
            'grease_pencil',
        ]
        data = scene_dumper.dump(pointer)

        scene_dumper.depth = 3

        scene_dumper.include_filter = ['children','objects','name']
        data['collection'] = scene_dumper.dump(pointer.collection)
        
        scene_dumper.depth = 1
        scene_dumper.include_filter = None
        
        data['eevee'] = scene_dumper.dump(pointer.eevee)
        data['cycles'] = scene_dumper.dump(pointer.cycles)        
        data['view_settings'] = scene_dumper.dump(pointer.view_settings)
        data['view_settings']['curve_mapping'] = scene_dumper.dump(pointer.view_settings.curve_mapping)
        
        if pointer.view_settings.use_curve_mapping:
            scene_dumper.depth = 5
            scene_dumper.include_filter = [
                'curves',
                'points',
                'location'
            ]
            data['view_settings']['curve_mapping']['curves'] = scene_dumper.dump(pointer.view_settings.curve_mapping.curves)
        
        
        return data

    def _resolve_deps_implementation(self):
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
