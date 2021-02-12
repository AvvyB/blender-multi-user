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


import logging
from pathlib import Path

import bpy
import mathutils
from deepdiff import DeepDiff
from replication.constants import DIFF_JSON, MODIFIED

from ..utils import flush_history
from .bl_collection import (dump_collection_children, dump_collection_objects,
                            load_collection_childrens, load_collection_objects,
                            resolve_collection_dependencies)
from .bl_datablock import BlDatablock
from .bl_file import get_filepath
from .dump_anything import Dumper, Loader

RENDER_SETTINGS = [
    'dither_intensity',
    'engine',
    'film_transparent',
    'filter_size',
    'fps',
    'fps_base',
    'frame_map_new',
    'frame_map_old',
    'hair_subdiv',
    'hair_type',
    'line_thickness',
    'line_thickness_mode',
    'metadata_input',
    'motion_blur_shutter',
    'pixel_aspect_x',
    'pixel_aspect_y',
    'preview_pixel_size',
    'preview_start_resolution',
    'resolution_percentage',
    'resolution_x',
    'resolution_y',
    'sequencer_gl_preview',
    'use_bake_clear',
    'use_bake_lores_mesh',
    'use_bake_multires',
    'use_bake_selected_to_active',
    'use_bake_user_scale',
    'use_border',
    'use_compositing',
    'use_crop_to_border',
    'use_file_extension',
    'use_freestyle',
    'use_full_sample',
    'use_high_quality_normals',
    'use_lock_interface',
    'use_motion_blur',
    'use_multiview',
    'use_sequencer',
    'use_sequencer_override_scene_strip',
    'use_single_layer',
    'views_format',
]

EVEE_SETTINGS = [
    'gi_diffuse_bounces',
    'gi_cubemap_resolution',
    'gi_visibility_resolution',
    'gi_irradiance_smoothing',
    'gi_glossy_clamp',
    'gi_filter_quality',
    'gi_show_irradiance',
    'gi_show_cubemaps',
    'gi_irradiance_display_size',
    'gi_cubemap_display_size',
    'gi_auto_bake',
    'taa_samples',
    'taa_render_samples',
    'use_taa_reprojection',
    'sss_samples',
    'sss_jitter_threshold',
    'use_ssr',
    'use_ssr_refraction',
    'use_ssr_halfres',
    'ssr_quality',
    'ssr_max_roughness',
    'ssr_thickness',
    'ssr_border_fade',
    'ssr_firefly_fac',
    'volumetric_start',
    'volumetric_end',
    'volumetric_tile_size',
    'volumetric_samples',
    'volumetric_sample_distribution',
    'use_volumetric_lights',
    'volumetric_light_clamp',
    'use_volumetric_shadows',
    'volumetric_shadow_samples',
    'use_gtao',
    'use_gtao_bent_normals',
    'use_gtao_bounce',
    'gtao_factor',
    'gtao_quality',
    'gtao_distance',
    'bokeh_max_size',
    'bokeh_threshold',
    'use_bloom',
    'bloom_threshold',
    'bloom_color',
    'bloom_knee',
    'bloom_radius',
    'bloom_clamp',
    'bloom_intensity',
    'use_motion_blur',
    'motion_blur_shutter',
    'motion_blur_depth_scale',
    'motion_blur_max',
    'motion_blur_steps',
    'shadow_cube_size',
    'shadow_cascade_size',
    'use_shadow_high_bitdepth',
    'gi_diffuse_bounces',
    'gi_cubemap_resolution',
    'gi_visibility_resolution',
    'gi_irradiance_smoothing',
    'gi_glossy_clamp',
    'gi_filter_quality',
    'gi_show_irradiance',
    'gi_show_cubemaps',
    'gi_irradiance_display_size',
    'gi_cubemap_display_size',
    'gi_auto_bake',
    'taa_samples',
    'taa_render_samples',
    'use_taa_reprojection',
    'sss_samples',
    'sss_jitter_threshold',
    'use_ssr',
    'use_ssr_refraction',
    'use_ssr_halfres',
    'ssr_quality',
    'ssr_max_roughness',
    'ssr_thickness',
    'ssr_border_fade',
    'ssr_firefly_fac',
    'volumetric_start',
    'volumetric_end',
    'volumetric_tile_size',
    'volumetric_samples',
    'volumetric_sample_distribution',
    'use_volumetric_lights',
    'volumetric_light_clamp',
    'use_volumetric_shadows',
    'volumetric_shadow_samples',
    'use_gtao',
    'use_gtao_bent_normals',
    'use_gtao_bounce',
    'gtao_factor',
    'gtao_quality',
    'gtao_distance',
    'bokeh_max_size',
    'bokeh_threshold',
    'use_bloom',
    'bloom_threshold',
    'bloom_color',
    'bloom_knee',
    'bloom_radius',
    'bloom_clamp',
    'bloom_intensity',
    'use_motion_blur',
    'motion_blur_shutter',
    'motion_blur_depth_scale',
    'motion_blur_max',
    'motion_blur_steps',
    'shadow_cube_size',
    'shadow_cascade_size',
    'use_shadow_high_bitdepth',
]

CYCLES_SETTINGS = [
    'shading_system',
    'progressive',
    'use_denoising',
    'denoiser',
    'use_square_samples',
    'samples',
    'aa_samples',
    'diffuse_samples',
    'glossy_samples',
    'transmission_samples',
    'ao_samples',
    'mesh_light_samples',
    'subsurface_samples',
    'volume_samples',
    'sampling_pattern',
    'use_layer_samples',
    'sample_all_lights_direct',
    'sample_all_lights_indirect',
    'light_sampling_threshold',
    'use_adaptive_sampling',
    'adaptive_threshold',
    'adaptive_min_samples',
    'min_light_bounces',
    'min_transparent_bounces',
    'caustics_reflective',
    'caustics_refractive',
    'blur_glossy',
    'max_bounces',
    'diffuse_bounces',
    'glossy_bounces',
    'transmission_bounces',
    'volume_bounces',
    'transparent_max_bounces',
    'volume_step_rate',
    'volume_max_steps',
    'dicing_rate',
    'max_subdivisions',
    'dicing_camera',
    'offscreen_dicing_scale',
    'film_exposure',
    'film_transparent_glass',
    'film_transparent_roughness',
    'filter_type',
    'pixel_filter_type',
    'filter_width',
    'seed',
    'use_animated_seed',
    'sample_clamp_direct',
    'sample_clamp_indirect',
    'tile_order',
    'use_progressive_refine',
    'bake_type',
    'use_camera_cull',
    'camera_cull_margin',
    'use_distance_cull',
    'distance_cull_margin',
    'motion_blur_position',
    'rolling_shutter_type',
    'rolling_shutter_duration',
    'texture_limit',
    'texture_limit_render',
    'ao_bounces',
    'ao_bounces_render',
]

VIEW_SETTINGS = [
    'look',
    'view_transform',
    'exposure',
    'gamma',
    'use_curve_mapping',
    'white_level',
    'black_level'
]


def dump_sequence(sequence: bpy.types.Sequence) -> dict:
    """ Dump a sequence to a dict

        :arg sequence: sequence to dump
        :type sequence: bpy.types.Sequence
        :return dict:
    """
    dumper = Dumper()
    dumper.exclude_filter = [
        'lock',
        'select',
        'select_left_handle',
        'select_right_handle',
        'strobe'
    ]
    dumper.depth = 1
    data = dumper.dump(sequence)


    # TODO: Support multiple images
    if sequence.type == 'IMAGE':
        data['filenames'] = [e.filename for e in sequence.elements]


    # Effect strip inputs
    input_count = getattr(sequence, 'input_count', None)
    if input_count:
        for n in range(input_count):
            input_name = f"input_{n+1}"
            data[input_name] = getattr(sequence, input_name).name

    return data


def load_sequence(sequence_data: dict, sequence_editor: bpy.types.SequenceEditor):
    """ Load sequence from dumped data

        :arg sequence_data: sequence to dump
        :type sequence_data:dict
        :arg sequence_editor: root sequence editor
        :type sequence_editor: bpy.types.SequenceEditor
    """
    strip_type = sequence_data.get('type')
    strip_name = sequence_data.get('name')
    strip_channel = sequence_data.get('channel')
    strip_frame_start = sequence_data.get('frame_start')

    sequence = sequence_editor.sequences_all.get(strip_name, None)

    if sequence is None:
        if strip_type == 'SCENE':
            strip_scene = bpy.data.scenes.get(sequence_data.get('scene'))
            sequence = sequence_editor.sequences.new_scene(strip_name,
                                                        strip_scene,
                                                        strip_channel,
                                                        strip_frame_start)
        elif strip_type == 'MOVIE':
            filepath = get_filepath(Path(sequence_data['filepath']).name)
            sequence = sequence_editor.sequences.new_movie(strip_name,
                                                        filepath,
                                                        strip_channel,
                                                        strip_frame_start)
        elif strip_type == 'SOUND':
            filepath = bpy.data.sounds[sequence_data['sound']].filepath
            sequence = sequence_editor.sequences.new_sound(strip_name,
                                                        filepath,
                                                        strip_channel,
                                                        strip_frame_start)
        elif strip_type == 'IMAGE':
            images_name = sequence_data.get('filenames')
            filepath = get_filepath(images_name[0])
            sequence = sequence_editor.sequences.new_image(strip_name,
                                                        filepath,
                                                        strip_channel,
                                                        strip_frame_start)
            # load other images
            if len(images_name)>1:
                for img_idx in range(1,len(images_name)):
                    sequence.elements.append((images_name[img_idx]))
        else:
            seq = {}

            for i in range(sequence_data['input_count']):
                seq[f"seq{i+1}"] = sequence_editor.sequences_all.get(sequence_data.get(f"input_{i+1}", None))

            sequence = sequence_editor.sequences.new_effect(name=strip_name,
                                                        type=strip_type,
                                                        channel=strip_channel,
                                                        frame_start=strip_frame_start,
                                                        frame_end=sequence_data['frame_final_end'],
                                                        **seq)

    loader = Loader()
    # TODO: Support filepath updates 
    loader.exclure_filter = ['filepath', 'sound', 'filenames','fps']
    loader.load(sequence, sequence_data)
    sequence.select = False


class BlScene(BlDatablock):
    bl_id = "scenes"
    bl_class = bpy.types.Scene
    bl_check_common = True
    bl_icon = 'SCENE_DATA'
    bl_reload_parent = False

    def _construct(self, data):
        instance = bpy.data.scenes.new(data["name"])
        instance.uuid = self.uuid

        return instance

    def _load_implementation(self, data, target):
        # Load other meshes metadata
        loader = Loader()
        loader.load(target, data)

        # Load master collection
        load_collection_objects(
            data['collection']['objects'], target.collection)
        load_collection_childrens(
            data['collection']['children'], target.collection)

        if 'world' in data.keys():
            target.world = bpy.data.worlds[data['world']]

        # Annotation
        if 'grease_pencil' in data.keys():
            target.grease_pencil = bpy.data.grease_pencils[data['grease_pencil']]

        if self.preferences.sync_flags.sync_render_settings:
            if 'eevee' in data.keys():
                loader.load(target.eevee, data['eevee'])

            if 'cycles' in data.keys():
                loader.load(target.cycles, data['cycles'])

            if 'render' in data.keys():
                loader.load(target.render, data['render'])

            if 'view_settings' in data.keys():
                loader.load(target.view_settings, data['view_settings'])
                if target.view_settings.use_curve_mapping and \
                        'curve_mapping' in data['view_settings']:
                    # TODO: change this ugly fix
                    target.view_settings.curve_mapping.white_level = data[
                        'view_settings']['curve_mapping']['white_level']
                    target.view_settings.curve_mapping.black_level = data[
                        'view_settings']['curve_mapping']['black_level']
                    target.view_settings.curve_mapping.update()

        # Sequencer
        sequences = data.get('sequences')
        
        if sequences:
            # Create sequencer data
            target.sequence_editor_create()
            vse = target.sequence_editor

            # Clear removed sequences
            for seq in vse.sequences_all:
                if seq.name not in sequences:
                    vse.sequences.remove(seq)
            # Load existing sequences
            for seq_name, seq_data in sequences.items():
                load_sequence(seq_data, vse)
        # If the sequence is no longer used, clear it
        elif target.sequence_editor and not sequences:
            target.sequence_editor_clear()

        # FIXME: Find a better way after the replication big refacotoring
        # Keep other user from deleting collection object by flushing their history
        flush_history()

    def _dump_implementation(self, data, instance=None):
        assert(instance)

        # Metadata
        scene_dumper = Dumper()
        scene_dumper.depth = 1
        scene_dumper.include_filter = [
            'name',
            'world',
            'id',
            'grease_pencil',
            'frame_start',
            'frame_end',
            'frame_step',
        ]
        if self.preferences.sync_flags.sync_active_camera:
            scene_dumper.include_filter.append('camera')

        data.update(scene_dumper.dump(instance))

        # Master collection
        data['collection'] = {}
        data['collection']['children'] = dump_collection_children(
            instance.collection)
        data['collection']['objects'] = dump_collection_objects(
            instance.collection)

        scene_dumper.depth = 1
        scene_dumper.include_filter = None

        # Render settings
        if self.preferences.sync_flags.sync_render_settings:
            scene_dumper.include_filter = RENDER_SETTINGS

            data['render'] = scene_dumper.dump(instance.render)

            if instance.render.engine == 'BLENDER_EEVEE':
                scene_dumper.include_filter = EVEE_SETTINGS
                data['eevee'] = scene_dumper.dump(instance.eevee)
            elif instance.render.engine == 'CYCLES':
                scene_dumper.include_filter = CYCLES_SETTINGS
                data['cycles'] = scene_dumper.dump(instance.cycles)

            scene_dumper.include_filter = VIEW_SETTINGS
            data['view_settings'] = scene_dumper.dump(instance.view_settings)

            if instance.view_settings.use_curve_mapping:
                data['view_settings']['curve_mapping'] = scene_dumper.dump(
                    instance.view_settings.curve_mapping)
                scene_dumper.depth = 5
                scene_dumper.include_filter = [
                    'curves',
                    'points',
                    'location',
                ]
                data['view_settings']['curve_mapping']['curves'] = scene_dumper.dump(
                    instance.view_settings.curve_mapping.curves)

        # Sequence
        vse = instance.sequence_editor
        if vse:
            dumped_sequences = {}
            for seq in vse.sequences_all:
                dumped_sequences[seq.name] = dump_sequence(seq)
            data['sequences'] = dumped_sequences


        return data

    def _resolve_deps_implementation(self):
        deps = []

        # Master Collection
        deps.extend(resolve_collection_dependencies(self.instance.collection))

        # world
        if self.instance.world:
            deps.append(self.instance.world)

        # annotations
        if self.instance.grease_pencil:
            deps.append(self.instance.grease_pencil)

        # Sequences
        vse = self.instance.sequence_editor
        if vse:
            for sequence in vse.sequences_all:
                if sequence.type == 'MOVIE' and sequence.filepath:
                    deps.append(Path(bpy.path.abspath(sequence.filepath)))
                elif sequence.type == 'SOUND' and sequence.sound:
                    deps.append(sequence.sound)
                elif sequence.type == 'IMAGE':
                    for elem in sequence.elements:
                        sequence.append(
                            Path(bpy.path.abspath(sequence.directory),
                            elem.filename))

        return deps

    def diff(self):
        exclude_path = []

        if not self.preferences.sync_flags.sync_render_settings:
            exclude_path.append("root['eevee']")
            exclude_path.append("root['cycles']")
            exclude_path.append("root['view_settings']")
            exclude_path.append("root['render']")

        if not self.preferences.sync_flags.sync_active_camera:
            exclude_path.append("root['camera']")

        return DeepDiff(self.data, self._dump(instance=self.instance), exclude_paths=exclude_path)
