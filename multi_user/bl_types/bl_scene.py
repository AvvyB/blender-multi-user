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
from .bl_collection import dump_collection_children, dump_collection_objects, load_collection_childrens, load_collection_objects
from ..utils import get_preferences

class BlScene(BlDatablock):
    bl_id = "scenes"
    bl_class = bpy.types.Scene
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = True
    bl_icon = 'SCENE_DATA'

    def _construct(self, data):
        instance = bpy.data.scenes.new(data["name"])
        return instance

    def _load_implementation(self, data, target):
        # Load other meshes metadata
        loader = Loader()
        loader.load(target, data)

        # Load master collection
        load_collection_objects(data['collection']['objects'], target.collection)
        load_collection_childrens(data['collection']['children'], target.collection)

        if 'world' in data.keys():
            target.world = bpy.data.worlds[data['world']]
        
        # Annotation
        if 'grease_pencil' in data.keys():
            target.grease_pencil = bpy.data.grease_pencils[data['grease_pencil']]

        if 'eevee' in data.keys():
            loader.load(target.eevee, data['eevee'])
        
        if 'cycles' in data.keys():
            loader.load(target.eevee, data['cycles'])

        if 'render' in data.keys():
            loader.load(target.render, data['render'])

        if 'view_settings' in data.keys():
            loader.load(target.view_settings, data['view_settings'])
            if target.view_settings.use_curve_mapping:
                #TODO: change this ugly fix
                target.view_settings.curve_mapping.white_level = data['view_settings']['curve_mapping']['white_level']
                target.view_settings.curve_mapping.black_level = data['view_settings']['curve_mapping']['black_level']
                target.view_settings.curve_mapping.update()

    def _dump_implementation(self, data, instance=None):
        assert(instance)
        data = {}

        scene_dumper = Dumper()
        scene_dumper.depth = 1
        scene_dumper.include_filter = [
            'name',
            'world',
            'id',
            'camera',
            'grease_pencil',
            'frame_start',
            'frame_end',
            'frame_step',
        ]
        data = scene_dumper.dump(instance)

        scene_dumper.depth = 3

        scene_dumper.include_filter = ['children','objects','name']
        data['collection'] = {}
        data['collection']['children'] = dump_collection_children(instance.collection)
        data['collection']['objects'] = dump_collection_objects(instance.collection)
        
        scene_dumper.depth = 1
        scene_dumper.include_filter = None
        
        pref = get_preferences()

        if pref.sync_flags.sync_render_settings:
            scene_dumper.exclude_filter = [
                'gi_cache_info',
                'feature_set',
                'debug_use_hair_bvh',
                'aa_samples',
                'blur_glossy',
                'glossy_bounces',
                'device',
                'max_bounces',
                'preview_aa_samples',
                'preview_samples',
                'sample_clamp_indirect',
                'samples',
                'volume_bounces',
                'file_extension',
                'use_denoising'
            ]
            data['eevee'] = scene_dumper.dump(instance.eevee)
            data['cycles'] = scene_dumper.dump(instance.cycles)        
            data['view_settings'] = scene_dumper.dump(instance.view_settings)
            data['render'] = scene_dumper.dump(instance.render)

            if instance.view_settings.use_curve_mapping:
                data['view_settings']['curve_mapping'] = scene_dumper.dump(instance.view_settings.curve_mapping)
                scene_dumper.depth = 5
                scene_dumper.include_filter = [
                    'curves',
                    'points',
                    'location'
                ]
                data['view_settings']['curve_mapping']['curves'] = scene_dumper.dump(instance.view_settings.curve_mapping.curves)
        
        
        return data

    def _resolve_deps_implementation(self):
        deps = []

        # child collections
        for child in self.instance.collection.children:
            deps.append(child)
        
        # childs objects
        for object in self.instance.objects:
            deps.append(object)
        
        # world
        if self.instance.world:
            deps.append(self.instance.world)
        
        # annotations
        if self.instance.grease_pencil:
            deps.append(self.instance.grease_pencil)

        return deps
