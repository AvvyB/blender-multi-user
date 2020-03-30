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

from ..libs.dump_anything import Dumper, Loader, load_collection_attr, dump_collection_attr
from ..libs.replication.replication.constants import DIFF_BINARY
from .bl_datablock import BlDatablock

logger = logging.getLogger(__name__)


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

    def load_implementation(self, data, target):
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
            load_collection_attr(target.vertices, 'co', data["verts_co"])
            load_collection_attr(target.edges, "vertices", data["egdes_vert"])
            if data['use_customdata_edge_crease']:
                load_collection_attr(
                    target.edges, "crease", data["edges_crease"])

            if data['use_customdata_edge_bevel']:
                load_collection_attr(
                    target.edges, "bevel_weight", data["edges_bevel"])

            load_collection_attr(
                target.loops, 'vertex_index', data["loop_vertex_index"])
            load_collection_attr(target.loops, 'normal', data["loop_normal"])
            load_collection_attr(
                target.polygons, 'loop_total', data["poly_loop_total"])
            load_collection_attr(
                target.polygons, 'loop_start', data["poly_loop_start"])
            load_collection_attr(
                target.polygons, 'use_smooth', data["poly_smooth"])
            load_collection_attr(
                target.polygons, 'material_index', data["poly_mat"])

            # UV Layers
            for layer in data['uv_layers']:
                if layer not in target.uv_layers:
                    target.uv_layers.new(name=layer)

                uv_buffer = np.frombuffer(data["uv_layers"][layer]['data'])

                target.uv_layers[layer].data.foreach_set('uv', uv_buffer)

            target.validate()
            target.update()

    def dump_implementation(self, data, pointer=None):
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
        data["verts_co"] = dump_collection_attr(mesh.vertices, 'co')

        # EDGES
        data["egdes_count"] = len(mesh.edges)
        data["egdes_vert"] = dump_collection_attr(mesh.edges, 'vertices')

        if mesh.use_customdata_edge_crease:
            data["edges_crease"] = dump_collection_attr(mesh.edges, 'crease')

        if mesh.use_customdata_edge_bevel:
            data["edges_bevel"] = dump_collection_attr(
                mesh.edges, 'edges_bevel')

        # POLYGONS
        data["poly_count"] = len(mesh.polygons)
        data["poly_mat"] = dump_collection_attr(
            mesh.polygons, 'material_index')
        data["poly_loop_start"] = dump_collection_attr(
            mesh.polygons, 'loop_start')
        data["poly_loop_total"] = dump_collection_attr(
            mesh.polygons, 'loop_total')
        data["poly_smooth"] = dump_collection_attr(mesh.polygons, 'use_smooth')

        # LOOPS
        data["loop_count"] = len(mesh.loops)
        data["loop_normal"] = dump_collection_attr(mesh.loops, 'normal')
        data["loop_vertex_index"] = dump_collection_attr(
            mesh.loops, 'vertex_index')

        # UV Layers
        data['uv_layers'] = {}
        for layer in mesh.uv_layers:
            data['uv_layers'][layer.name] = {}
            data['uv_layers'][layer.name]['data'] = dump_collection_attr(
                layer.data, 'uv')

        # Fix material index
        m_list = []
        for material in pointer.materials:
            if material:
                m_list.append(material.name)

        data['material_list'] = m_list

        return data

    def resolve_deps_implementation(self):
        deps = []

        for material in self.pointer.materials:
            if material:
                deps.append(material)

        return deps
