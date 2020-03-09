import bpy
import bmesh
import mathutils

from .. import utils
from ..libs.replication.replication.constants import DIFF_BINARY
from .bl_datablock import BlDatablock


def dump_mesh(mesh, data={}):
    import bmesh

    mesh_data = data
    mesh_buffer = bmesh.new()

    # https://blog.michelanders.nl/2016/02/copying-vertices-to-numpy-arrays-in_4.html
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
        v['normal'] = list(vert.normal)
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
        f["smooth"] = face.smooth
        f["normal"] = list(face.normal)
        f["index"] = face.index

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
    # return mesh_data


class BlMesh(BlDatablock):
    bl_id = "meshes"
    bl_class = bpy.types.Mesh
    bl_delay_refresh = 10
    bl_delay_apply = 10
    bl_automatic_push = True
    bl_icon = 'MESH_DATA'

    def construct(self, data):
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

    def is_valid(self):
        return bpy.data.meshes.get(self.data['name'])
