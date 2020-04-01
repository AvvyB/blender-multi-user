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
from .bl_datablock import BlDatablock

# GPencil data api is structured as it follow: 
# GP-Object --> GP-Layers --> GP-Frames --> GP-Strokes --> GP-Stroke-Points

STROKE_POINT = [
    'co',
    'pressure',
    'strength',
    'uv_factor',
    'uv_rotation'

]

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

    loader = Loader()
    loader.load(stroke, stroke_data)

    stroke.points.add(stroke_data["p_count"])

    np_load_collection(stroke_data['points'], stroke.points, STROKE_POINT)

def dump_frame(frame):
    """ Dump a grease pencil frame to a dict

        :param frame: target grease pencil stroke
        :type frame: bpy.types.GPencilFrame
        :return: dict
    """

    assert(frame)

    dumped_frame = dict()
    dumped_frame['frame_number'] = frame.frame_number
    dumped_frame['strokes'] = []
    
    # TODO: took existing strokes in account
    for stroke in frame.strokes:
        dumped_frame['strokes'].append(dump_stroke(stroke))
    
    return dumped_frame


def load_frame(frame_data, frame):
    """ Load a grease pencil frame from a dict

        :param frame_data: source grease pencil frame
        :type frame_data: dict
        :param frame: target grease pencil stroke
        :type frame: bpy.types.GPencilFrame
    """

    assert(frame and frame_data)

    # frame.frame_number = frame_data['frame_number']

    # TODO: took existing stroke in account

    for stroke_data in frame_data['strokes']:
        target_stroke = frame.strokes.new()
        load_stroke(stroke_data, target_stroke)


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
        'thickness',
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



class BlGpencil(BlDatablock):
    bl_id = "grease_pencils"
    bl_class = bpy.types.GreasePencil
    bl_delay_refresh = 2
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'GREASEPENCIL'

    def _construct(self, data):
        return bpy.data.grease_pencils.new(data["name"])

    def _load_implementation(self, data, target):
        target.materials.clear()
        if "materials" in data.keys():
            for mat in data['materials']:
                target.materials.append(bpy.data.materials[mat])

        # TODO: reuse existing layer
        for layer in target.layers:
            target.layers.remove(layer)

        if "layers" in data.keys():
            for layer in data["layers"]:
                layer_data = data["layers"].get(layer)

                # if layer not in target.layers.keys():
                target_layer = target.layers.new(data["layers"][layer]["info"])
                # else:
                #     target_layer = target.layers[layer]
                #     target_layer.clear()

                load_layer(layer_data, target_layer)
        
        loader = Loader()
        loader.load(target, data)



    def _dump_implementation(self, data, pointer=None):
        assert(pointer)
        dumper = Dumper()
        dumper.depth = 2
        data = dumper.dump(pointer)

        data['layers'] = {}
        
        for layer in pointer.layers:
            data['layers'][layer.info] = dump_layer(layer)

        return data

    def _resolve_deps_implementation(self):
        deps = []

        for material in self.pointer.materials:
            deps.append(material)

        return deps
