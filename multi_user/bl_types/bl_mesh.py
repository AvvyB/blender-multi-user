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
import bmesh
import mathutils
import logging
import numpy as np

from .dump_anything import Dumper, Loader, np_load_collection_primitives, np_dump_collection_primitive, np_load_collection, np_dump_collection
from replication.constants import DIFF_BINARY
from replication.exception import ContextError
from replication.protocol import ReplicatedDatablock

from .bl_datablock import get_datablock_from_uuid
from .bl_material import dump_materials_slots, load_materials_slots
from ..utils import get_preferences
from .bl_datablock import resolve_datablock_from_uuid
from .bl_action import dump_animation_data, load_animation_data, resolve_animation_dependencies

VERTICE = ['co']

EDGE = [
    'vertices',
    'crease',
    'bevel_weight',
    'use_seam',
    'use_edge_sharp',
]
LOOP = [
    'vertex_index',
    'normal',
]

POLYGON = [
    'loop_total',
    'loop_start',
    'use_smooth',
    'material_index',
]

class BlMesh(ReplicatedDatablock):
    use_delta = True

    bl_id = "meshes"
    bl_class = bpy.types.Mesh
    bl_check_common = False
    bl_icon = 'MESH_DATA'
    bl_reload_parent = True

    @staticmethod
    def construct(data: dict) -> object:
        return bpy.data.meshes.new(data.get("name"))

    @staticmethod
    def load(data: dict, datablock: object):
        if not datablock or datablock.is_editmode:
            raise ContextError
        else:
            load_animation_data(data.get('animation_data'), datablock)

            loader = Loader()
            loader.load(datablock, data)

            # MATERIAL SLOTS
            src_materials = data.get('materials', None)
            if src_materials:
                load_materials_slots(src_materials, datablock.materials)

            # CLEAR GEOMETRY
            if datablock.vertices:
                datablock.clear_geometry()

            datablock.vertices.add(data["vertex_count"])
            datablock.edges.add(data["egdes_count"])
            datablock.loops.add(data["loop_count"])
            datablock.polygons.add(data["poly_count"])

            # LOADING
            np_load_collection(data['vertices'], datablock.vertices, VERTICE)
            np_load_collection(data['edges'], datablock.edges, EDGE)
            np_load_collection(data['loops'], datablock.loops, LOOP)
            np_load_collection(data["polygons"],datablock.polygons, POLYGON)

            # UV Layers
            if 'uv_layers' in data.keys():
                for layer in data['uv_layers']:
                    if layer not in datablock.uv_layers:
                        datablock.uv_layers.new(name=layer)

                    np_load_collection_primitives(
                        datablock.uv_layers[layer].data, 
                        'uv', 
                        data["uv_layers"][layer]['data'])
            
            # Vertex color
            if 'vertex_colors' in data.keys():
                for color_layer in data['vertex_colors']:
                    if color_layer not in datablock.vertex_colors:
                        datablock.vertex_colors.new(name=color_layer)

                    np_load_collection_primitives(
                        datablock.vertex_colors[color_layer].data, 
                        'color', 
                        data["vertex_colors"][color_layer]['data'])

            datablock.validate()
            datablock.update()

    @staticmethod
    def dump(datablock: object) -> dict:
        if (datablock.is_editmode or bpy.context.mode == "SCULPT") and not get_preferences().sync_flags.sync_during_editmode:
            raise ContextError("Mesh is in edit mode")
        mesh = datablock

        dumper = Dumper()
        dumper.depth = 1
        dumper.include_filter = [
            'name',
            'use_auto_smooth',
            'auto_smooth_angle',
            'use_customdata_edge_bevel',
            'use_customdata_edge_crease'
        ]

        data = dumper.dump(mesh)

        data['animation_data'] = dump_animation_data(datablock)

        # VERTICES
        data["vertex_count"] = len(mesh.vertices)
        data["vertices"] = np_dump_collection(mesh.vertices, VERTICE)

        # EDGES
        data["egdes_count"] = len(mesh.edges)
        data["edges"] = np_dump_collection(mesh.edges, EDGE)

        # POLYGONS
        data["poly_count"] = len(mesh.polygons)
        data["polygons"] = np_dump_collection(mesh.polygons, POLYGON)

        # LOOPS
        data["loop_count"] = len(mesh.loops)
        data["loops"] = np_dump_collection(mesh.loops, LOOP)

        # UV Layers
        if mesh.uv_layers:
            data['uv_layers'] = {}
            for layer in mesh.uv_layers:
                data['uv_layers'][layer.name] = {}
                data['uv_layers'][layer.name]['data'] = np_dump_collection_primitive(layer.data, 'uv')

        # Vertex color
        if mesh.vertex_colors:
            data['vertex_colors'] = {}
            for color_map in mesh.vertex_colors:
                data['vertex_colors'][color_map.name] = {}
                data['vertex_colors'][color_map.name]['data'] = np_dump_collection_primitive(color_map.data, 'color')

        # Materials
        data['materials'] = dump_materials_slots(datablock.materials)
        return data
    
    @staticmethod
    def resolve_deps(datablock: object) -> [object]:
        deps = []

        for material in datablock.materials:
            if material:
                deps.append(material)

        deps.extend(resolve_animation_dependencies(datablock))

        return deps

    @staticmethod
    def resolve(data: dict) -> object:
        uuid = data.get('uuid')
        return resolve_datablock_from_uuid(uuid, bpy.data.meshes)

    @staticmethod
    def needs_update(datablock: object, data: dict) -> bool:
        return ('EDIT' not in bpy.context.mode and bpy.context.mode != 'SCULPT') \
            or get_preferences().sync_flags.sync_during_editmode

_type = bpy.types.Mesh
_class = BlMesh
