import bpy
import bmesh
import mathutils

from .. import utils
from .bl_datablock import BlDatablock

def dump_mesh(mesh, data={}):
    import bmesh

    mesh_data = data
    mesh_buffer = bmesh.new()

    mesh_buffer.from_mesh(mesh)

    uv_layer = mesh_buffer.loops.layers.uv.verify()
    bevel_layer = mesh_buffer.verts.layers.bevel_weight.verify()
    skin_layer = mesh_buffer.verts.layers.skin.verify()

    verts = {}
    for vert in mesh_buffer.verts:
        v = {}
        v["co"] = list(vert.co)

        # vert metadata
        v['bevel'] = vert[bevel_layer]
        # v['skin'] = list(vert[skin_layer])

        verts[str(vert.index)] = v

    mesh_data["verts"] = verts

    edges = {}
    for edge in mesh_buffer.edges:
        e = {}
        e["verts"] = [edge.verts[0].index, edge.verts[1].index]

        # Edge metadata
        e["smooth"] = edge.smooth

        edges[edge.index] = e
    mesh_data["edges"] = edges

    faces = {}
    for face in mesh_buffer.faces:
        f = {}
        fverts = []
        for vert in face.verts:
            fverts.append(vert.index)

        f["verts"] = fverts
        f["material_index"] = face.material_index

        uvs = []
        # Face metadata
        for loop in face.loops:
            loop_uv = loop[uv_layer]

            uvs.append(list(loop_uv.uv))

        f["uv"] = uvs
        faces[face.index] = f

    mesh_data["faces"] = faces

    uv_layers = []
    for uv_layer in mesh.uv_layers:
        uv_layers.append(uv_layer.name)

    mesh_data["uv_layers"] = uv_layers
    return mesh_data

class BlMesh(BlDatablock):
    def __init__(self, *args, **kwargs):
        self.icon = 'MESH_DATA'
        
        super().__init__( *args, **kwargs)
    
    def construct(self, data):
        return bpy.data.meshes.new(data["name"])

    def load(self, data, target):
        if not target or not target.is_editmode:
            # 1 - LOAD GEOMETRY
            mesh_buffer = bmesh.new()
    
            for i in data["verts"]:
                v = mesh_buffer.verts.new(data["verts"][i]["co"])
    
            mesh_buffer.verts.ensure_lookup_table()
    
            for i in data["edges"]:
                verts = mesh_buffer.verts
                v1 = data["edges"][i]["verts"][0]
                v2 = data["edges"][i]["verts"][1]
                mesh_buffer.edges.new([verts[v1], verts[v2]])
    
            for p in data["faces"]:
                verts = []
                for v in data["faces"][p]["verts"]:
                    verts.append(mesh_buffer.verts[v])
    
                if len(verts) > 0:
                    f = mesh_buffer.faces.new(verts)
    
                    uv_layer = mesh_buffer.loops.layers.uv.verify()
    
                    f.material_index = data["faces"][p]['material_index']
    
                    # UV loading
                    for i, loop in enumerate(f.loops):
                        loop_uv = loop[uv_layer]
                        loop_uv.uv = data["faces"][p]["uv"][i]
    
   
            mesh_buffer.to_mesh(target)
    
            # mesh_buffer.from_mesh(target)
    
            # 2 - LOAD METADATA
    
            # uv's
            for uv_layer in data['uv_layers']:
                target.uv_layers.new(name=uv_layer)
    
            bevel_layer = mesh_buffer.verts.layers.bevel_weight.verify()
            skin_layer = mesh_buffer.verts.layers.skin.verify()
    
            # for face in mesh_buffer.faces:
    
            #     # Face metadata
            #     for loop in face.loops:
            #         loop_uv = loop[uv_layer]
            #         loop_uv.uv = data['faces'][face.index]["uv"]
    
            utils.dump_anything.load(target, data)
    
            # 3 - LOAD MATERIAL SLOTS
            material_to_load = []
            material_to_load = utils.revers(data["materials"])
            target.materials.clear()
            # SLots
            i = 0
    
            for m in data["material_list"]:
                target.materials.append(bpy.data.materials[m])

    def dump(self, pointer=None):
        assert(pointer)

        data = utils.dump_datablock(pointer, 2)
        data = dump_mesh(pointer, data)
        # Fix material index
        m_list = []
        for m in pointer.materials:
            m_list.append(m.name)

        data['material_list'] = m_list

        return data

    def resolve(self):
        assert(self.buffer)      
        self.pointer = bpy.data.meshes.get(self.buffer['name'])

    def diff(self):
        return (self.bl_diff() or
                len(self.pointer.vertices) != len(self.buffer['verts']))

    def resolve_dependencies(self):
        deps = []
        
        for material in self.pointer.materials:
            deps.append(material)
        
        return deps
        
bl_id = "meshes"
bl_class = bpy.types.Mesh
bl_rep_class = BlMesh
bl_delay_refresh = 10
bl_delay_apply = 10
