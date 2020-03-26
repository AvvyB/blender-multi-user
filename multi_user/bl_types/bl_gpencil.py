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

from ..libs import dump_anything 
from .bl_datablock import BlDatablock

# GPencil data api is structured as it follow: 
# GP-Object --> GP-Layers --> GP-Frames --> GP-Strokes --> GP-Stroke-Points

def dump_stroke(stroke):
    """ Dump a grease pencil stroke to a dict

        :param stroke: target grease pencil stroke
        :type stroke: bpy.types.GPencilStroke
        :return: dict
    """
<
    assert(stroke)

    dumper = dump_anything.Dumper()
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
    dumped_stroke = dump_anything.dump(stroke)

    # Stoke points
    p_count = len(stroke.points)
    dumped_stroke['p_count'] = p_count
    
    p_co = np.empty(p_count*3, dtype=np.float64)
    stroke.points.foreach_get('co', p_co)

    p_pressure = np.empty(p_count, dtype=np.float64)
    stroke.points.foreach_get('pressure', p_pressure)

    p_strength = np.empty(p_count, dtype=np.float64)
    stroke.points.foreach_get('strength', p_strength)

    p_vertex_color = np.empty(p_count*4, dtype=np.float64)
    stroke.points.foreach_get('vertex_color', p_vertex_color)

    # TODO: uv_factor, uv_rotation

    dumped_stroke['p_co'] = p_co.tobytes()
    dumped_stroke['p_pressure'] = p_pressure.tobytes()
    dumped_stroke['p_strength'] = p_strength.tobytes()
    dumped_stroke['p_vertex_color'] = p_vertex_color.tobytes()

    return dumped_stroke

def load_stroke(stroke_data, stroke):
    """ Load a grease pencil stroke from a dict

        :param stroke_data: dumped grease pencil stroke 
        :type stroke_data: dict
        :param stroke: target grease pencil stroke
        :type stroke: bpy.types.GPencilStroke
    """
    assert(stroke and stroke_data)

    dump_anything.load(stroke, stroke_data)

    p_co = np.frombuffer(stroke_data["p_co"], dtype=np.float64)
    p_pressure = np.frombuffer(stroke_data["p_pressure"], dtype=np.float64)
    p_strength = np.frombuffer(stroke_data["p_strength"], dtype=np.float64)
    p_vertex_color = np.frombuffer(stroke_data["p_vertex_color"], dtype=np.float64)
    
    stroke.points.add(stroke_data["p_count"])

    stroke.points.foreach_set('co', p_co)
    stroke.points.foreach_set('pressure', p_pressure)
    stroke.points.foreach_set('strength', p_strength)
    stroke.points.foreach_set('vertex_color', p_vertex_color)


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

    frame.frame_number = frame_data['frame_number']

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

    dumper = dump_anything.Dumper()

    dumper.exclude_filter = [
        'parent_type'
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
    dump_anything.load(layer, layer_data)

    for frame_data in layer_data["frames"]:
        target_frame = layer.frames.new(frame_data['frame_number'])

        load_frame(frame_data, target_frame)



class BlGpencil(BlDatablock):
    bl_id = "grease_pencils"
    bl_class = bpy.types.GreasePencil
    bl_delay_refresh = 5
    bl_delay_apply = 5
    bl_automatic_push = True
    bl_icon = 'GREASEPENCIL'

    def _construct(self, data):
        return bpy.data.grease_pencils.new(data["name"])

    def load_implementation(self, data, target):
        for layer in target.layers:
            target.layers.remove(layer)

        target.materials.clear()
        if "materials" in data.keys():
            for mat in data['materials']:
                target.materials.append(bpy.data.materials[mat])

        if "layers" in data.keys():
            for layer in data["layers"]:
                layer_data = data["layers"].get(layer)

                if layer not in target.layers.keys():
                    target_layer = target.layers.new(data["layers"][layer]["info"])
                else:
                    target_layer = target.layers[layer]

                load_layer(layer_data, target_layer)

        dump_anything.load(target, data)



    def dump_implementation(self, data, pointer=None):
        assert(pointer)
        data = dump_anything.dump(pointer, 2)

        data['layers'] = {}
        
        for layer in pointer.layers:
            data['layers'][layer.info] = dump_layer(layer)

        return data

    def resolve_deps_implementation(self):
        deps = []

        for material in self.pointer.materials:
            deps.append(material)

        return deps
