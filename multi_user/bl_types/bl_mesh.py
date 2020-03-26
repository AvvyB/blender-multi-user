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

from .. import utils
from ..libs.replication.replication.constants import DIFF_BINARY
from .bl_datablock import BlDatablock

logger = logging.getLogger(__name__)


class BlMesh(BlDatablock):
    bl_id = "meshes"
    bl_class = bpy.types.Mesh
    bl_delay_refresh = 10
    bl_delay_apply = 10
    bl_automatic_push = True
    bl_icon = 'MESH_DATA'

    def _construct(self, data):
        instance = bpy.data.meshes.new(data["name"])
        instance.uuid = self.uuid
        return instance

    def load_implementation(self, data, target):
        if not target or not target.is_editmode:
            utils.dump_anything.load(target, data)
            
            # MATERIAL SLOTS
            target.materials.clear()

            for m in data["material_list"]:
                target.materials.append(bpy.data.materials[m])

            # CLEAR GEOMETRY
            if target.vertices:
                target.clear_geometry()

            # VERTS
            vertices = np.frombuffer(data["verts_co"], dtype=np.float64)
            vert_count = int(len(vertices)/3)
            target.vertices.add(vert_count)

            # EDGES

            egdes_vert = np.frombuffer(data["egdes_vert"], dtype=np.int)
            
            edge_count = data["egdes_count"]
            target.edges.add(edge_count)
            
    

            # LOOPS
            loops_count = data["loop_count"]
            target.loops.add(loops_count)

            loop_vertex_index = np.frombuffer(
                data['loop_vertex_index'], dtype=np.int)
            loop_normal = np.frombuffer(data['loop_normal'], dtype=np.float64)

            # POLY
            poly_count = data["poly_count"]
            target.polygons.add(poly_count)

            poly_loop_start = np.frombuffer(
                data["poly_loop_start"], dtype=np.int)
            poly_loop_total = np.frombuffer(
                data["poly_loop_total"], dtype=np.int)
            poly_smooth = np.frombuffer(data["poly_smooth"], dtype=np.bool)

            poly_mat = np.frombuffer(data["poly_mat"], dtype=np.int)

            # LOADING 
            target.vertices.foreach_set('co', vertices)
            target.edges.foreach_set("vertices", egdes_vert)
            
            if data['use_customdata_edge_crease']:
                edges_crease = np.frombuffer(data["edges_crease"], dtype=np.float64)
                target.edges.foreach_set("crease", edges_crease)
            
            if data['use_customdata_edge_bevel']:
                edges_bevel = np.frombuffer(data["edges_bevel"], dtype=np.float64)
                target.edges.foreach_set("bevel_weight", edges_bevel)

            target.loops.foreach_set("vertex_index", loop_vertex_index)
            target.loops.foreach_set("normal", loop_normal)
            target.polygons.foreach_set("loop_total", poly_loop_total)
            target.polygons.foreach_set("loop_start", poly_loop_start)
            target.polygons.foreach_set("use_smooth", poly_smooth)
            target.polygons.foreach_set("material_index", poly_mat)
            
            
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

        dumper = utils.dump_anything.Dumper()
        dumper.depth = 1
        dumper.include_filter = [
            'name',
            'use_auto_smooth',
            'auto_smooth_angle',
            'use_customdata_edge_bevel',
            'use_customdata_edge_crease'
        ]

        data = dumper.dump(mesh)

        # TODO: selective dump
        # VERTICES
        vert_count = len(mesh.vertices)

        verts_co = np.empty(vert_count*3, dtype=np.float64)
        mesh.vertices.foreach_get('co', verts_co)
        data["verts_co"] = verts_co.tobytes()

        # EDGES 
        edge_count = len(mesh.edges)

        edges_vert = np.empty(edge_count*2, dtype=np.int)
        mesh.edges.foreach_get('vertices', edges_vert)
        data["egdes_vert"] = edges_vert.tobytes()
        data["egdes_count"] = len(mesh.edges)

        if mesh.use_customdata_edge_crease:
            edges_crease = np.empty(edge_count, dtype=np.float64)
            mesh.edges.foreach_get('crease', edges_crease)
            data["edges_crease"] = edges_crease.tobytes()

        if mesh.use_customdata_edge_bevel:
            edges_bevel = np.empty(edge_count, dtype=np.float64)
            mesh.edges.foreach_get('bevel_weight', edges_bevel)
            data["edges_bevel"] = edges_bevel.tobytes()

        # POLYGONS
        poly_count = len(mesh.polygons)
        data["poly_count"] = poly_count

        poly_mat = np.empty(poly_count, dtype=np.int)
        mesh.polygons.foreach_get("material_index", poly_mat)
        data["poly_mat"] = poly_mat.tobytes()

        poly_loop_start = np.empty(poly_count, dtype=np.int)
        mesh.polygons.foreach_get("loop_start", poly_loop_start)
        data["poly_loop_start"] = poly_loop_start.tobytes()

        poly_loop_total = np.empty(poly_count, dtype=np.int)
        mesh.polygons.foreach_get("loop_total", poly_loop_total)
        data["poly_loop_total"] = poly_loop_total.tobytes()

        poly_smooth = np.empty(poly_count, dtype=np.bool)
        mesh.polygons.foreach_get("use_smooth", poly_smooth)
        data["poly_smooth"] = poly_smooth.tobytes()

        # LOOPS
        loop_count = len(mesh.loops)
        data["loop_count"] = loop_count

        loop_normal = np.empty(loop_count*3, dtype=np.float64)
        mesh.loops.foreach_get("normal", loop_normal)
        data["loop_normal"] = loop_normal.tobytes()

        loop_vertex_index = np.empty(loop_count, dtype=np.int)
        mesh.loops.foreach_get("vertex_index", loop_vertex_index)
        data["loop_vertex_index"] = loop_vertex_index.tobytes()

        # UV Layers
        data['uv_layers'] = {}
        for layer in mesh.uv_layers:
            data['uv_layers'][layer.name] = {}

            uv_layer = np.empty(len(layer.data)*2, dtype=np.float64)
            layer.data.foreach_get("uv", uv_layer)

            data['uv_layers'][layer.name]['data'] = uv_layer.tobytes()

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
