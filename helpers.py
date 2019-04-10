import bpy
from .libs import dump_anything

def dump_datablock(datablock, depth):
    if datablock:
        print("sending {}".format(datablock.name))

        dumper = dump_anything.Dumper()
        dumper.type_subset = dumper.match_subset_all
        dumper.depth = depth

        datablock_type = datablock.bl_rna.name
        key = "{}/{}".format(datablock_type, datablock.name)
        data = dumper.dump(datablock)

        client.push_update(key, datablock_type, data)


def dump_datablock_attibute(datablock, attributes, depth=1):
    if datablock:
        dumper = dump_anything.Dumper()
        dumper.type_subset = dumper.match_subset_all
        dumper.depth = depth

        datablock_type = datablock.bl_rna.name
        key = "{}/{}".format(datablock_type, datablock.name)

        data = {}
        for attr in attributes:
            try:
                data[attr] = dumper.dump(getattr(datablock, attr))
            except:
                pass

        client.push_update(key, datablock_type, data)


def upload_mesh(mesh):
    if mesh.bl_rna.name == 'Mesh':
        dump_datablock_attibute(
            mesh, ['name', 'polygons', 'edges', 'vertices'], 6)


def upload_material(material):
    if material.bl_rna.name == 'Material':
        dump_datablock_attibute(material, ['name', 'node_tree'], 7)


def upload_gpencil(gpencil):
    if gpencil.bl_rna.name == 'Grease Pencil':
        dump_datablock_attibute(gpencil, ['name', 'layers','materials'], 9)


def load_mesh(target=None, data=None, create=False):
    import bmesh

    # TODO: handle error
    mesh_buffer = bmesh.new()

    for i in data["vertices"]:
        mesh_buffer.verts.new(data["vertices"][i]["co"])

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
            mesh_buffer.faces.new(verts)

    if target is None and create:
        target = bpy.data.meshes.new(data["name"])

    mesh_buffer.to_mesh(target)

    # Load other meshes metadata
    dump_anything.load(target, data)


def load_object(target=None, data=None, create=False):
    try:
        if target is None and create:
            pointer = None

            # Object specific constructor...
            if data["data"] in bpy.data.meshes.keys():
                pointer = bpy.data.meshes[data["data"]]
            elif data["data"] in bpy.data.lights.keys():
                pointer = bpy.data.lights[data["data"]]
            elif data["data"] in bpy.data.cameras.keys():
                pointer = bpy.data.cameras[data["data"]]
            elif data["data"] in bpy.data.curves.keys():
                pointer = bpy.data.curves[data["data"]]
            elif data["data"] in bpy.data.grease_pencils.keys():
                pointer = bpy.data.grease_pencils[data["data"]]

            target = bpy.data.objects.new(data["name"], pointer)

        # Load other meshes metadata
        dump_anything.load(target, data)
        import mathutils
        target.matrix_world = mathutils.Matrix(data["matrix_world"])

    except:
        print("Object {} loading error ".format(data["name"]))


def load_collection(target=None, data=None, create=False):
    try:
        if target is None and create:
            target = bpy.data.collections.new(data["name"])

        # Load other meshes metadata
        # dump_anything.load(target, data)

        # load objects into collection
        for object in data["objects"]:
            target.objects.link(bpy.data.objects[object])

        for object in target.objects.keys():
            if object not in data["objects"]:
                target.objects.unlink(bpy.data.objects[object])
    except:
        print("Collection loading error")


def load_scene(target=None, data=None, create=False):
    try:
        if target is None and create:
            target = bpy.data.scenes.new(data["name"])

        # Load other meshes metadata
        dump_anything.load(target, data)

        # Load master collection
        for object in data["collection"]["objects"]:
            if object not in target.collection.objects.keys():
                target.collection.objects.link(bpy.data.objects[object])

        for object in target.collection.objects.keys():
            if object not in  data["collection"]["objects"]:
                target.collection.objects.unlink(bpy.data.objects[object])
        # load collections
        # TODO: Recursive link
        for collection in data["collection"]["children"]:
            if collection not in target.collection.children.keys():
                target.collection.children.link(
                    bpy.data.collections[collection])
        
        # Load annotation
        if data["grease_pencil"]:
            target.grease_pencil = bpy.data.grease_pencils[data["grease_pencil"]["name"]]
    except:
        print("Scene loading error")


def load_material(target=None, data=None, create=False):
    try:
        if target is None and create:
            target = bpy.data.materials.new(data["name"])

        # Load other meshes metadata
        dump_anything.load(target, data)

        # load nodes
        for node in data["node_tree"]["nodes"]:
            index = target.node_tree.nodes.find(node)

            if index is -1:
                node_type = data["node_tree"]["nodes"][node]["bl_idname"]

                target.node_tree.nodes.new(type=node_type)

            dump_anything.load(
                target.node_tree.nodes[index], data["node_tree"]["nodes"][node])

            for input in data["node_tree"]["nodes"][node]["inputs"]:

                try:
                    target.node_tree.nodes[index].inputs[input].default_value = data[
                        "node_tree"]["nodes"][node]["inputs"][input]["default_value"]
                except:
                    pass

        # Load nodes links
        target.node_tree.links.clear()

        for link in data["node_tree"]["links"]:
            current_link = data["node_tree"]["links"][link]
            input_socket = target.node_tree.nodes[current_link['to_node']
                                                  ['name']].inputs[current_link['to_socket']['name']]
            output_socket = target.node_tree.nodes[current_link['from_node']
                                                   ['name']].outputs[current_link['from_socket']['name']]

            target.node_tree.links.new(input_socket, output_socket)

    except:
        print("Material loading error")


def load_gpencil_layer(target=None,data=None, create=False):
    
    dump_anything.load(target, data)


    for frame in data["frames"]:
        try: 
            tframe = target.frames[frame]
        except:
            tframe = target.frames.new(frame)
        dump_anything.load(tframe, data["frames"][frame])
        for stroke in data["frames"][frame]["strokes"]:
            try:
                tstroke = tframe.strokes[stroke]
            except:
                tstroke = tframe.strokes.new()
            dump_anything.load(tstroke, data["frames"][frame]["strokes"][stroke])
            
            for point in data["frames"][frame]["strokes"][stroke]["points"]:
                p = data["frames"][frame]["strokes"][stroke]["points"][point]
                try:
                    tpoint = tstroke.points[point]
                except:
                    tpoint = tstroke.points.add(1)
                    tpoint = tstroke.points[len(tstroke.points)-1]
                dump_anything.load(tpoint, p)    
        

def load_gpencil(target=None, data=None, create=False):
    try:
        if target is None and create:
            target = bpy.data.grease_pencils.new(data["name"])

        if "layers" in data.keys():
            for layer in data["layers"]:
                if layer not in target.layers.keys():
                    gp_layer = target.layers.new(data["layers"][layer]["info"])
                else:
                    gp_layer = target.layers[layer]
                load_gpencil_layer(target=gp_layer,data=data["layers"][layer],create=create)
        # Load other meshes metadata
        dump_anything.load(target, data)
    except:
        print("default loading error")


def load_light(target=None, data=None, create=False, type=None):
    try:
        if target is None and create:
            bpy.data.lights.new(data["name"], data["type"])

        # Load other meshes metadata
        dump_anything.load(target, data)
    except:
        print("light loading error")


def load_default(target=None, data=None, create=False, type=None):
    try:
        if target is None and create:
            getattr(bpy.data, CORRESPONDANCE[type]).new(data["name"])

        # Load other meshes metadata
        dump_anything.load(target, data)
    except:
        print("default loading error")
