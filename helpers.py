import bpy
import mathutils
from .libs import dump_anything
from uuid import uuid4
import logging

CORRESPONDANCE = {'Collection': 'collections', 'Mesh': 'meshes', 'Object': 'objects', 'Material': 'materials',
                  'Texture': 'textures', 'Scene': 'scenes', 'Light': 'lights', 'Camera': 'cameras', 'Action': 'actions', 'Armature': 'armatures', 'Grease Pencil': 'grease_pencils'}

SUPPORTED_TYPES = ['Material',
                   'Texture', 'Light', 'Camera', 'Mesh', 'Grease Pencil', 'Object', 'Action', 'Armature', 'Collection', 'Scene']

logger = logging.getLogger(__name__)

# UTILITY FUNCTIONS
def refresh_window():
    import bpy
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)


def get_selected_objects(scene):
    selected_objects = []
    for obj in scene.objects:
        if obj.select_get():
            selected_objects.append(obj.name)

    return selected_objects

def get_all_datablocks():
    datas = []
    for datatype in SUPPORTED_TYPES:
        for item in getattr(bpy.data, CORRESPONDANCE[datatype]):
            item.id= bpy.context.scene.session_settings.username
            datas.append("{}/{}".format(datatype, item.name))
    
    return datas
            
#    LOAD HELPERS
def load(key, value):
    target = resolve_bpy_path(key)
    target_type = key.split('/')[0]

    if value == "None":
        return 
    
    if target_type == 'Object':
        load_object(target=target, data=value,
                    create=True)
    elif target_type == 'Mesh':
        load_mesh(target=target, data=value,
                  create=True)
    elif target_type == 'Collection':
        load_collection(target=target, data=value,
                        create=True)
    elif target_type == 'Material':
        load_material(target=target, data=value,
                      create=True)
    elif target_type == 'Grease Pencil':
        load_gpencil(target=target, data=value,
                     create=True)
    elif target_type == 'Scene':
        load_scene(target=target, data=value,
                   create=True)
    elif 'Light' in target_type:
        load_light(target=target, data=value,
                   create=True)
    elif target_type == 'Camera':
        load_default(target=target, data=value,
                     create=True, type=target_type)
    elif target_type == 'Client':
        load_client(key.split('/')[1], value)


def resolve_bpy_path(path):
    """
    Get bpy property value from path
    """
    item = None

    try:
        path = path.split('/')
        item = getattr(bpy.data, CORRESPONDANCE[path[0]])[path[1]]

    except:
        pass

    return item


def load_client(client=None, data=None):
    C = bpy.context
    D = bpy.data
    
    if client and data:
        # localy_selected = get_selected_objects(C.scene)
        # Draw client

        client_data = data
        # Load selected object
        # for obj in C.scene.objects:
        #     if obj.id == client:
        #          D.objects[obj.name].hide_select = True
        #     else:
        #         D.objects[obj.name].hide_select = False
            # if client_data['active_objects'] and obj.name in client_data['active_objects']:
            #     D.objects[obj.name].hide_select = True
            # else:
            #     D.objects[obj.name].hide_select = False       


def load_mesh(target=None, data=None, create=False):
    import bmesh

    if not target or not target.is_editmode:
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

        target.id = data['id']
    else:
        logger.debug("Mesh can't be loaded")


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

        target.matrix_world = mathutils.Matrix(data["matrix_world"])

        target.id = data['id']

    except:
        print("Object {} loading error ".format(data["name"]))


def load_collection(target=None, data=None, create=False):
    try:
        if target is None and create:
            target = bpy.data.collections.new(data["name"])

        # Load other meshes metadata
        # dump_anything.load(target, data)

        # link objects
        for object in data["objects"]:
            target.objects.link(bpy.data.objects[object])

        for object in target.objects.keys():
            if object not in data["objects"]:
                target.objects.unlink(bpy.data.objects[object])
        
        # Link childrens
        for collection in data["children"]:
            if collection not in target.children.keys():
                target.children.link(
                    bpy.data.collections[collection])
        
        target.id = data['id']
    except Exception as e:
        print("Collection loading error: {}".format(e))


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
            if object not in data["collection"]["objects"]:
                target.collection.objects.unlink(bpy.data.objects[object])
        # load collections
        # TODO: Recursive link
        for collection in data["collection"]["children"]:
            if collection not in target.collection.children.keys():
                target.collection.children.link(
                    bpy.data.collections[collection])

        target.id = data['id']
        # Load annotation
        # if data["grease_pencil"]:
        #     target.grease_pencil = bpy.data.grease_pencils[data["grease_pencil"]["name"]]
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

        target.id = data['id']

        for link in data["node_tree"]["links"]:
            current_link = data["node_tree"]["links"][link]
            input_socket = target.node_tree.nodes[current_link['to_node']
                                                  ['name']].inputs[current_link['to_socket']['name']]
            output_socket = target.node_tree.nodes[current_link['from_node']
                                                   ['name']].outputs[current_link['from_socket']['name']]

            target.node_tree.links.new(input_socket, output_socket)

    except:
        print("Material loading error")


def load_gpencil_layer(target=None, data=None, create=False):

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
            dump_anything.load(
                tstroke, data["frames"][frame]["strokes"][stroke])

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
                load_gpencil_layer(
                    target=gp_layer, data=data["layers"][layer], create=create)

        dump_anything.load(target, data)

        target.id = data['id']
    except:
        print("default loading error")


def load_light(target=None, data=None, create=False, type=None):
    try:
        if target is None and create:
            bpy.data.lights.new(data["name"], data["type"])


        dump_anything.load(target, data)

        target.id = data['id']
    except:
        print("light loading error")


def load_default(target=None, data=None, create=False, type=None):
    try:
        if target is None and create:
            getattr(bpy.data, CORRESPONDANCE[type]).new(data["name"])

        dump_anything.load(target, data)

        target.id = data['id']
    except:
        print("default loading error")

# DUMP HELPERS
def dump(key):
    target = resolve_bpy_path(key)
    target_type = key.split('/')[0]
    data = None


    if target_type == 'Material':
        data = dump_datablock_attibute(target, ['name', 'node_tree','id'], 7)
    elif target_type == 'Grease Pencil':
        data = dump_datablock_attibute(
            target, ['name', 'layers', 'materials','id'], 9)
    elif target_type == 'Camera':
        data = dump_datablock(target, 1)
    elif target_type == 'Light':
        data = dump_datablock(target, 1)
    elif target_type == 'Mesh':
        data = dump_datablock_attibute(
            target, ['name', 'polygons', 'edges', 'vertices','id'], 6)
    elif target_type == 'Object':
        data = dump_datablock(target, 1)
    elif target_type == 'Collection':
        data = dump_datablock(target, 4)
    elif target_type == 'Scene':
        data = dump_datablock_attibute(target,['name','collection','id','camera','grease_pencil'], 4)

    return data


def dump_datablock(datablock, depth):
    if datablock:
        dumper = dump_anything.Dumper()
        dumper.type_subset = dumper.match_subset_all
        dumper.depth = depth

        datablock_type = datablock.bl_rna.name
        key = "{}/{}".format(datablock_type, datablock.name)
        data = dumper.dump(datablock)

        return data


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

        return data


def init_client(key=None):
    client_dict = {}

    C = bpy.context
    Net = C.scene.session_settings
    client_dict['uuid'] = str(uuid4())
    client_dict['location'] = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
    client_dict['color'] = [Net.client_color.r,
                            Net.client_color.g, Net.client_color.b, 1]

    client_dict['active_objects'] = get_selected_objects(C.view_layer)

    return client_dict
