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
from ..libs.replication.replication.constants import DIFF_BINARY
from .bl_datablock import BlDatablock

logger = logging.getLogger(__name__)

VERTICE = ['co']

EDGE = [
    'vertices',
    'crease',
    'bevel_weight',
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

class BlMesh(BlDatablock):
    bl_id = "meshes"
    bl_class = bpy.types.Mesh
    bl_delay_refresh = 2
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'MESH_DATA'

    def _construct(self, data):
        instance = bpy.data.meshes.new(data["name"])
        instance.uuid = self.uuid
        return instance

    def _load_implementation(self, data, target):
        if not target or not target.is_editmode:
            loader = Loader()
            loader.load(target, data)

            # MATERIAL SLOTS
            target.materials.clear()

            for m in data["material_list"]:
                target.materials.append(bpy.data.materials[m])

            # CLEAR GEOMETRY
            if target.vertices:
                target.clear_geometry()

            target.vertices.add(data["vertex_count"])
            target.edges.add(data["egdes_count"])
            target.loops.add(data["loop_count"])
            target.polygons.add(data["poly_count"])

            # LOADING
            np_load_collection(data['vertices'], target.vertices, VERTICE)
            np_load_collection(data['edges'], target.edges, EDGE)
            np_load_collection(data['loops'], target.loops, LOOP)
            np_load_collection(data["polygons"],target.polygons, POLYGON)

            # UV Layers
            for layer in data['uv_layers']:
                if layer not in target.uv_layers:
                    target.uv_layers.new(name=layer)

                np_load_collection_primitives(
                    target.uv_layers[layer].data, 
                    'uv', 
                    data["uv_layers"][layer]['data'])
            
            # Vertex color
            for color_layer in data['vertex_colors']:
                if color_layer not in target.vertex_colors:
                    target.vertex_colors.new(name=color_layer)

                np_load_collection_primitives(
                    target.vertex_colors[color_layer].data, 
                    'color', 
                    data["vertex_colors"][color_layer]['data'])

            target.validate()
            target.update()

    def _dump_implementation(self, data, pointer=None):
        assert(pointer)

        mesh = pointer

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
        data['uv_layers'] = {}
        for layer in mesh.uv_layers:
            data['uv_layers'][layer.name] = {}
            data['uv_layers'][layer.name]['data'] = np_dump_collection_primitive(layer.data, 'uv')

        # Vertex color
        data['vertex_colors'] = {}
        for color_map in mesh.vertex_colors:
            data['vertex_colors'][color_map.name] = {}
            data['vertex_colors'][color_map.name]['data'] = np_dump_collection_primitive(color_map.data, 'color')

        # Fix material index
        m_list = []
        for material in pointer.materials:
            if material:
                m_list.append(material.name)

        data['material_list'] = m_list

        return data

    def _resolve_deps_implementation(self):
        deps = []

        for material in self.pointer.materials:
            if material:
                deps.append(material)

        return deps
