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
from .bl_datablock import BlDatablock, get_datablock_from_uuid

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
    bl_check_common = False
    bl_icon = 'MESH_DATA'

    def _construct(self, data):
        instance = bpy.data.meshes.new(data["name"])
        instance.uuid = self.uuid
        return instance

    def _load_implementation(self, data, target):
        if not target or target.is_editmode:
            raise ContextError
        else:
            loader = Loader()
            loader.load(target, data)

            # MATERIAL SLOTS
            target.materials.clear()

            for mat_uuid, mat_name in data["material_list"]:
                mat_ref = None
                if mat_uuid is not None:
                    mat_ref = get_datablock_from_uuid(mat_uuid, None)
                else:
                    mat_ref = bpy.data.materials.get(mat_name, None)

                if mat_ref is None:
                    raise Exception("Material doesn't exist")

                target.materials.append(mat_ref)

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
            if 'uv_layers' in data.keys():
                for layer in data['uv_layers']:
                    if layer not in target.uv_layers:
                        target.uv_layers.new(name=layer)

                    np_load_collection_primitives(
                        target.uv_layers[layer].data, 
                        'uv', 
                        data["uv_layers"][layer]['data'])
            
            # Vertex color
            if 'vertex_colors' in data.keys():
                for color_layer in data['vertex_colors']:
                    if color_layer not in target.vertex_colors:
                        target.vertex_colors.new(name=color_layer)

                    np_load_collection_primitives(
                        target.vertex_colors[color_layer].data, 
                        'color', 
                        data["vertex_colors"][color_layer]['data'])

            target.validate()
            target.update()

    def _dump_implementation(self, data, instance=None):
        assert(instance)

        if instance.is_editmode and not self.preferences.sync_flags.sync_during_editmode:
            raise ContextError("Mesh is in edit mode")
        mesh = instance

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

        # Fix material index
        m_list = []
        for material in instance.materials:
            if material:
                m_list.append((material.uuid,material.name))

        data['material_list'] = m_list

        return data

    def _resolve_deps_implementation(self):
        deps = []

        for material in self.instance.materials:
            if material:
                deps.append(material)

        return deps
