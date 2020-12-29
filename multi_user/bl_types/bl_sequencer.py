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
from pathlib import Path
import logging

from .bl_file import get_filepath
from .dump_anything import Loader, Dumper
from .bl_datablock import BlDatablock, get_datablock_from_uuid

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
    loader.load(sequence, sequence_data)
    sequence.select = False


class BlSequencer(BlDatablock):
    bl_id = "scenes"
    bl_class = bpy.types.SequenceEditor
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = True
    bl_icon = 'SEQUENCE'
    bl_reload_parent = False

    def _construct(self, data):
        # Get the scene
        scene_id = data.get('name')
        scene = bpy.data.scenes.get(scene_id, None)

        # Create sequencer data
        scene.sequence_editor_clear()
        scene.sequence_editor_create()

        return scene.sequence_editor

    def resolve(self, construct = True):
        scene = bpy.data.scenes.get(self.data['name'], None)
        if scene:
            if scene.sequence_editor is None and construct:
                self.instance = self._construct(self.data)
            else:
                self.instance = scene.sequence_editor
        else:
            logging.warning("Sequencer editor scene not found")

    def _load_implementation(self, data, target):
        loader = Loader()
        # Sequencer
        sequences = data.get('sequences')
        if sequences:
            for seq in target.sequences_all:
                if seq.name not in sequences:
                    target.sequences.remove(seq)
            for seq_name, seq_data in sequences.items():
                load_sequence(seq_data, target)

    def _dump_implementation(self, data, instance=None):
        assert(instance)
        sequence_dumper = Dumper()
        sequence_dumper.depth = 1
        sequence_dumper.include_filter = [
            'proxy_storage',
        ]
        data = {}#sequence_dumper.dump(instance)
        # Sequencer
        sequences = {}

        for seq in instance.sequences_all:
            sequences[seq.name] = dump_sequence(seq)

        data['sequences'] = sequences
        data['name'] = instance.id_data.name

        return data


    def _resolve_deps_implementation(self):
        deps = []

        for seq in self.instance.sequences_all:
            if seq.type == 'MOVIE' and seq.filepath:
                deps.append(Path(bpy.path.abspath(seq.filepath)))
            elif seq.type == 'SOUND' and seq.sound:
                deps.append(seq.sound)
            elif seq.type == 'IMAGE':
                for e in seq.elements:
                    deps.append(Path(bpy.path.abspath(seq.directory), e.filename))
        return deps
