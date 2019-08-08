import bpy
import bmesh
import mathutils

from .. import utils
from ..libs.replication.data import ReplicatedDatablock

class BlMesh(ReplicatedDatablock):
    def load(self, data, target):
        if not target or not target.is_editmode:
            # LOAD GEOMETRY
            mesh_buffer = bmesh.new()
    
            for i in data["vertices"]:
               v =  mesh_buffer.verts.new(data["vertices"][i]["co"])
               v.normal = data["vertices"][i]["normal"]
    
            mesh_buffer.verts.ensure_lookup_table()
    
            for i in data["edges"]:
                verts = mesh_buffer.verts
                v1 = data["edges"][i]["vertices"][0]
                v2 = data["edges"][i]["vertices"][1]
                mesh_buffer.edges.new([verts[v1], verts[v2]])
    
            for p in data["polygons"]:
                verts = []
                for v in data["polygons"][p]["vertices"]:
                    verts.append(mesh_buffer.verts[v])
    
                if len(verts) > 0:
                    f = mesh_buffer.faces.new(verts)
                    f.material_index = data["polygons"][p]['material_index']
    
            if target is None and create:
                target = bpy.data.meshes.new(data["name"])
    
            mesh_buffer.to_mesh(target)
    
            # LOAD METADATA
            # dump_anything.load(target, data)
    
            material_to_load = []
            material_to_load = utils.revers(data["materials"])
            target.materials.clear()
            # SLots
            i = 0
    
            for m in data["material_list"]:
                target.materials.append(bpy.data.materials[m])
    
            target.id = data['id']

    def dump(self, pointer=None):
        assert(pointer)

        data = utils.dump_datablock(pointer, 2)
        utils.dump_datablock_attibute(
            pointer, ['name', 'polygons', 'edges', 'vertices', 'id'], 6, data)
        
        # Fix material index
        m_list = []
        for m in pointer.materials:
            m_list.append(m.name)

        data['material_list'] = m_list

        return data

bl_id = "meshes"
bl_class = bpy.types.Mesh
bl_rep_class = BlMesh 

