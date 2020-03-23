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

def dump_mesh(mesh, data={}):
    import bmesh

    mesh_data = data
    # https://blog.michelanders.nl/2016/02/copying-vertices-to-numpy-arrays-in_4.html

    # VERTICES
    start = utils.current_milli_time()

    vert_count = len(mesh.vertices)
    shape = (vert_count, 3) 

    verts_co = np.empty(vert_count*3, dtype=np.float64)
    mesh.vertices.foreach_get('co', verts_co)
    # verts_co.shape = shape
    mesh_data["verts_co"] = verts_co.tobytes()

    verts_normal = np.empty(vert_count*3, dtype=np.float64)
    mesh.vertices.foreach_get('normal', verts_normal)
    # verts_normal.shape = shape
    mesh_data["verts_normal"] = verts_normal.tobytes()
    
    verts_bevel = np.empty(vert_count, dtype=np.float64)
    mesh.vertices.foreach_get('bevel_weight', verts_bevel)
    mesh_data["verts_bevel"] = verts_bevel.tobytes()

    logger.error(f"verts {utils.current_milli_time()-start} ms")
    
    # EDGES
    start = utils.current_milli_time()
    edge_count = len(mesh.edges)
    
    edges_vert = np.empty(edge_count*2, dtype=np.int)
    mesh.edges.foreach_get('vertices', edges_vert)
    # edges_vert.shape = (edge_count, 2)
    mesh_data["egdes_vert"] = edges_vert.tobytes()

    logger.error(f"edges {utils.current_milli_time()-start} ms")

    start = utils.current_milli_time()

    # POLYGONS
    start = utils.current_milli_time()
    poly_count = len(mesh.polygons)

    poly_mat = np.empty(poly_count, dtype=np.int)
    mesh.polygons.foreach_get("material_index", poly_mat)
    mesh_data["poly_mat"] = poly_mat.tobytes()

    poly_loop_start = np.empty(poly_count, dtype=np.int)
    mesh.polygons.foreach_get("loop_start", poly_loop_start)
    mesh_data["poly_loop_start"] = poly_loop_start.tobytes()

    poly_loop_total = np.empty(poly_count, dtype=np.int)
    mesh.polygons.foreach_get("loop_total", poly_loop_total)
    mesh_data["poly_loop_total"] = poly_loop_total.tobytes()

    poly_smooth = np.empty(poly_count, dtype=np.bool)
    mesh.polygons.foreach_get("use_smooth", poly_smooth)
    mesh_data["poly_smooth"] = poly_smooth.tobytes()
    
    logger.error(f"polygons {utils.current_milli_time()-start} ms")

    # UV
    start = utils.current_milli_time()
    mesh_data['uv_layers'] = {}
    for layer in mesh.uv_layers:
        mesh_data['uv_layers'][layer.name] = {}
        
        uv_layer = np.empty(len(layer.data)*2, dtype=np.float64)
        layer.data.foreach_get("uv", uv_layer)

        mesh_data['uv_layers'][layer.name]['data'] = uv_layer.tobytes()

    logger.error(f"uvs {utils.current_milli_time()-start} ms")

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
             # 1 - LOAD MATERIAL SLOTS
            # SLots
            i = 0

            for m in data["material_list"]:
                target.materials.append(bpy.data.materials[m])

            # 2 - LOAD GEOMETRY
            mesh_buffer = bmesh.new()

            for i in data["verts"]:
                v = mesh_buffer.verts.new(data["verts"][i]["co"])
                v.normal = data["verts"][i]["normal"]
            mesh_buffer.verts.ensure_lookup_table()

            for i in data["edges"]:
                verts = mesh_buffer.verts
                v1 = data["edges"][i]["verts"][0]
                v2 = data["edges"][i]["verts"][1]
                edge = mesh_buffer.edges.new([verts[v1], verts[v2]])
                edge.smooth = data["edges"][i]["smooth"]
            
            mesh_buffer.edges.ensure_lookup_table()
            for p in data["faces"]:
                verts = []
                for v in data["faces"][p]["verts"]:
                    verts.append(mesh_buffer.verts[v])

                if len(verts) > 0:
                    f = mesh_buffer.faces.new(verts)

                    uv_layer = mesh_buffer.loops.layers.uv.verify()

                    f.smooth = data["faces"][p]["smooth"]
                    f.normal = data["faces"][p]["normal"]
                    f.index = data["faces"][p]["index"]
                    f.material_index = data["faces"][p]['material_index']
                    # UV loading
                    for i, loop in enumerate(f.loops):
                        loop_uv = loop[uv_layer]
                        loop_uv.uv = data["faces"][p]["uv"][i]
            mesh_buffer.faces.ensure_lookup_table()
            mesh_buffer.to_mesh(target)

            # 3 - LOAD METADATA
            # uv's
            utils.dump_anything.load(target.uv_layers, data['uv_layers'])

            bevel_layer = mesh_buffer.verts.layers.bevel_weight.verify()
            skin_layer = mesh_buffer.verts.layers.skin.verify()

            utils.dump_anything.load(target, data)

    def dump_implementation(self, data, pointer=None):
        assert(pointer)

        dumper = utils.dump_anything.Dumper()
        dumper.depth = 2
        dumper.include_filter = [
            'name',
            'use_auto_smooth',
            'auto_smooth_angle'
        ]

        
        data = dumper.dump(pointer)
        
        dump_mesh(pointer, data)
        
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
