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
import numpy as np

from .dump_anything import  (Dumper, 
                                    Loader,
                                    np_dump_collection,
                                    np_load_collection)
from replication.protocol import ReplicatedDatablock
from .bl_datablock import resolve_datablock_from_uuid
from .bl_action import dump_animation_data, load_animation_data, resolve_animation_dependencies
from ..utils import get_preferences


STROKE_POINT = [
    'co',
    'pressure',
    'strength',
    'uv_factor',
    'uv_rotation'

]

STROKE = [
    "aspect",
    "display_mode",
    "end_cap_mode",
    "hardness",
    "line_width",
    "material_index",
    "start_cap_mode",
    "uv_rotation",
    "uv_scale",
    "uv_translation",
    "vertex_color_fill",
]
if bpy.app.version[1] >= 91:
    STROKE.append('use_cyclic')
else:
    STROKE.append('draw_cyclic')

if bpy.app.version[1] >= 83:
    STROKE_POINT.append('vertex_color')

def dump_stroke(stroke):
    """ Dump a grease pencil stroke to a dict

        :param stroke: target grease pencil stroke
        :type stroke: bpy.types.GPencilStroke
        :return: dict
    """

    assert(stroke)

    dumper = Dumper()
    dumper.include_filter = [
        "aspect",
        "display_mode",
        "draw_cyclic",
        "end_cap_mode",
        "hardeness",
        "line_width",
        "material_index",
        "start_cap_mode",
        "uv_rotation",
        "uv_scale",
        "uv_translation",
        "vertex_color_fill",
    ]
    dumped_stroke = dumper.dump(stroke)

    # Stoke points
    p_count = len(stroke.points)
    dumped_stroke['p_count'] = p_count
    dumped_stroke['points'] = np_dump_collection(stroke.points, STROKE_POINT)

    # TODO: uv_factor, uv_rotation

    return dumped_stroke


def load_stroke(stroke_data, stroke):
    """ Load a grease pencil stroke from a dict

        :param stroke_data: dumped grease pencil stroke 
        :type stroke_data: dict
        :param stroke: target grease pencil stroke
        :type stroke: bpy.types.GPencilStroke
    """
    assert(stroke and stroke_data)

    stroke.points.add(stroke_data["p_count"])
    np_load_collection(stroke_data['points'], stroke.points, STROKE_POINT)

    # HACK: Temporary fix to trigger a BKE_gpencil_stroke_geometry_update to 
    # fix fill issues
    stroke.uv_scale = stroke_data["uv_scale"]


def dump_frame(frame):
    """ Dump a grease pencil frame to a dict

        :param frame: target grease pencil stroke
        :type frame: bpy.types.GPencilFrame
        :return: dict
    """

    assert(frame)

    dumped_frame = dict()
    dumped_frame['frame_number'] = frame.frame_number
    dumped_frame['strokes'] = np_dump_collection(frame.strokes, STROKE)
    dumped_frame['strokes_points'] = []

    for stroke in frame.strokes:
        dumped_frame['strokes_points'].append(dump_stroke(stroke))
    
    return dumped_frame


def load_frame(frame_data, frame):
    """ Load a grease pencil frame from a dict

        :param frame_data: source grease pencil frame
        :type frame_data: dict
        :param frame: target grease pencil stroke
        :type frame: bpy.types.GPencilFrame
    """

    assert(frame and frame_data)

    for stroke_data in frame_data['strokes_points']:
        target_stroke = frame.strokes.new()
        load_stroke(stroke_data, target_stroke)

    np_load_collection(frame_data['strokes'], frame.strokes, STROKE)


def dump_layer(layer):
    """ Dump a grease pencil layer

        :param layer: target grease pencil stroke
        :type layer: bpy.types.GPencilFrame
    """

    assert(layer)

    dumper = Dumper()

    dumper.include_filter = [
        'info',
        'opacity',
        'channel_color',
        'color',
        # 'thickness', #TODO: enabling only for annotation
        'tint_color',
        'tint_factor',
        'vertex_paint_opacity',
        'line_change',
        'use_onion_skinning',
        'use_annotation_onion_skinning',
        'annotation_onion_before_range',
        'annotation_onion_after_range',
        'annotation_onion_before_color',
        'annotation_onion_after_color',
        'pass_index',
        # 'viewlayer_render',
        'blend_mode',
        'hide',
        'annotation_hide',
        'lock',
        # 'lock_frame',
        # 'lock_material',
        # 'use_mask_layer',
        'use_lights',
        'use_solo_mode',
        'select',
        'show_points',
        'show_in_front',
        # 'parent',
        # 'parent_type',
        # 'parent_bone',
        # 'matrix_inverse',
    ]
    if layer.id_data.is_annotation:
        dumper.include_filter.append('thickness')

    dumped_layer = dumper.dump(layer)

    dumped_layer['frames'] = []

    for frame in layer.frames:
        dumped_layer['frames'].append(dump_frame(frame))

    return dumped_layer


def load_layer(layer_data, layer):
    """ Load a grease pencil layer from a dict

        :param layer_data: source grease pencil layer data
        :type layer_data: dict
        :param layer: target grease pencil stroke
        :type layer: bpy.types.GPencilFrame
    """
    # TODO: take existing data in account
    loader = Loader()
    loader.load(layer, layer_data)

    for frame_data in layer_data["frames"]:
        target_frame = layer.frames.new(frame_data['frame_number'])

        load_frame(frame_data, target_frame)


def layer_changed(datablock: object, data: dict) -> bool:
    if datablock.layers.active and \
            datablock.layers.active.info != data["active_layers"]:
        return True
    else:
        return False


def frame_changed(data: dict) -> bool:
    return bpy.context.scene.frame_current != data["eval_frame"]

class BlGpencil(ReplicatedDatablock):
    bl_id = "grease_pencils"
    bl_class = bpy.types.GreasePencil
    bl_check_common = False
    bl_icon = 'GREASEPENCIL'
    bl_reload_parent = False

    @staticmethod
    def construct(data: dict) -> object:
        return bpy.data.grease_pencils.new(data["name"])

    @staticmethod
    def load(data: dict, datablock: object):
        datablock.materials.clear()
        if "materials" in data.keys():
            for mat in data['materials']:
                datablock.materials.append(bpy.data.materials[mat])

        loader = Loader()
        loader.load(datablock, data)

        # TODO: reuse existing layer
        for layer in datablock.layers:
            datablock.layers.remove(layer)

        if "layers" in data.keys():
            for layer in data["layers"]:
                layer_data = data["layers"].get(layer)

                # if layer not in datablock.layers.keys():
                target_layer = datablock.layers.new(data["layers"][layer]["info"])
                # else:
                #     target_layer = target.layers[layer]
                #     target_layer.clear()

                load_layer(layer_data, target_layer)

            datablock.layers.update()

    @staticmethod
    def dump(datablock: object) -> dict:
        dumper = Dumper()
        dumper.depth = 2
        dumper.include_filter = [
            'materials',
            'name',
            'zdepth_offset',
            'stroke_thickness_space',
            'pixel_factor',
            'stroke_depth_order'
        ]
        data = dumper.dump(datablock)

        data['layers'] = {}

        for layer in datablock.layers:
            data['layers'][layer.info] = dump_layer(layer)

        data["active_layers"] = datablock.layers.active.info if datablock.layers.active else "None"
        data["eval_frame"] = bpy.context.scene.frame_current
        return data

    @staticmethod
    def resolve(data: dict) -> object:
        uuid = data.get('uuid')
        name = data.get('name')
        datablock = resolve_datablock_from_uuid(uuid, bpy.data.grease_pencils)
        if datablock is None:
            datablock = bpy.data.grease_pencils.get(name)

        return datablock

    @staticmethod
    def resolve_deps(datablock: object) -> [object]:
        deps = []

        for material in datablock.materials:
            deps.append(material)

        return deps

    @staticmethod
    def needs_update(datablock: object, data: dict) -> bool:
        return bpy.context.mode == 'OBJECT' \
            or layer_changed(datablock, data) \
            or frame_changed(data) \
            or get_preferences().sync_flags.sync_during_editmode

_type = bpy.types.GreasePencil
_class = BlGpencil
