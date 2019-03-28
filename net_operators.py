import logging
import random
import string
import time
import asyncio
import queue

import bgl
import blf
import bpy
import gpu
import mathutils
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader

from . import net_components, net_ui, rna_translation
from .libs import dump_anything

logger = logging.getLogger(__name__)

client = None
server = None
context = None

TASKS  =  []

COLOR_TABLE = [(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1),
               (0, 0.5, 1, 1), (0.5, 0, 1, 1)]
SUPPORTED_DATABLOCKS = ['collections', 'meshes', 'objects',
                        'materials', 'textures', 'lights', 'cameras', 'actions', 'armatures','grease_pencils']
SUPPORTED_TYPES = ['Collection', 'Mesh', 'Object', 'Material',
                   'Texture', 'Light', 'Camera', 'Action', 'Armature','GreasePencil','Scene']

CORRESPONDANCE = {'Collection':'collections', 'Mesh':'meshes', 'Object':'objects', 'Material':'materials',
                   'Texture':'textures','Scene':'scenes', 'Light':'lights', 'Camera':'cameras', 'Action':'actions', 'Armature':'armatures','GreasePencil':'grease_pencils'}
# UTILITY FUNCTIONS


def clean_scene(elements=SUPPORTED_DATABLOCKS):
    for datablock in elements:
        datablock_ref = getattr(bpy.data, datablock)
        for item in datablock_ref:
            datablock_ref.remove(item)


def view3d_find():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    return area, region, rv3d

                    break

    return None, None, None


def get_target(region, rv3d, coord):
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    target = ray_origin + view_vector
    return [target.x, target.y, target.z]


def get_client_view_rect():
    area, region, rv3d = view3d_find()

    v1 = [0, 0, 0]
    v2 = [0, 0, 0]
    v3 = [0, 0, 0]
    v4 = [0, 0, 0]

    width = region.width
    height = region.height

    v1 = get_target(region, rv3d, (0, 0))
    v3 = get_target(region, rv3d, (0, height))
    v2 = get_target(region, rv3d, (width, height))
    v4 = get_target(region, rv3d, (width, 0))

    coords = (v1, v2, v3, v4)
    indices = (
        (1, 3), (2, 1), (3, 0), (2, 0)
    )
    return coords


def get_client_view_rect():
    area, region, rv3d = view3d_find()

    v1 = [0, 0, 0]
    v2 = [0, 0, 0]
    v3 = [0, 0, 0]
    v4 = [0, 0, 0]

    width = region.width
    height = region.height

    v1 = get_target(region, rv3d, (0, 0))
    v3 = get_target(region, rv3d, (0, height))
    v2 = get_target(region, rv3d, (width, height))
    v4 = get_target(region, rv3d, (width, 0))

    coords = (v1, v2, v3, v4)
    indices = (
        (1, 3), (2, 1), (3, 0), (2, 0)
    )
    return coords


def get_client_2d(coords):
    area, region, rv3d = view3d_find()

    return view3d_utils.location_3d_to_region_2d(region, rv3d, coords)


def randomStringDigits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


def resolve_bpy_path(path):
    """
    Get bpy property value from path
    """
    path = path.split('/')
    item = None

    try:
        item = getattr(bpy.data, CORRESPONDANCE[path[0]])[path[1]]

    except:
        pass

    return item


def refresh_window():
    import bpy
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

def dump_datablock(datablock,depth):
    if datablock:
        print("sending {}".format(datablock.name))

        dumper = dump_anything.Dumper()
        dumper.type_subset = dumper.match_subset_all
        dumper.depth = depth

        datablock_type = datablock.bl_rna.name
        key = "{}/{}".format(datablock_type,datablock.name)
        data = dumper.dump(datablock)

        client.push_update(key, datablock_type, data)

def dump_datablock_attibute(datablock,attributes,depth=1):
    if datablock:
        print("sending {}".format(datablock.name))

        dumper = dump_anything.Dumper()
        dumper.type_subset = dumper.match_subset_all
        dumper.depth = depth

        datablock_type = datablock.bl_rna.name
        key = "{}/{}".format(datablock_type,datablock.name)

        data = {}
        for attr in attributes:
            try:
                data[attr] = dumper.dump(getattr(datablock,attr))
            except:
                pass

        client.push_update(key, datablock_type, data)

def upload_mesh(mesh):
    if mesh.bl_rna.name == 'Mesh':
        dump_datablock_attibute(mesh,['name','polygons','edges','vertices'],6)

def init_scene():
    for cam in bpy.data.cameras:
        dump_datablock(cam,1)
    for light in bpy.data.lights:
        dump_datablock(light,1)
    for mat in bpy.data.materials:
        dump_datablock(mat,7)
    for mesh in bpy.data.meshes:
        upload_mesh(mesh)
    for object in bpy.data.objects:
        dump_datablock(object,1)
    for collection in bpy.data.collections:
        dump_datablock(collection,4)
    for scene in bpy.data.scenes:
        dump_datablock(scene,4)

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
    except:
        print("Collection loading error")


def load_scene(target=None, data=None, create=False):
    try:
        if target is None and create:
            target = bpy.data.scenes.new(data["name"])

        # Load other meshes metadata
        # dump_anything.load(target, data)

        #Load master collection
        for object in data["collection"]["objects"]:
            if object not in target.collection.objects.keys():
                target.collection.objects.link(bpy.data.objects[object])

        # load collections 
        # TODO: Recursive link
        for collection in data["collection"]["children"]:
            if collection not in target.collection.children.keys():
                target.collection.children.link(bpy.data.collections[collection])
    except:
        print("Collection loading error")


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
            print(target.node_tree.nodes[current_link['to_node']['name']])
            input_socket = target.node_tree.nodes[current_link['to_node']
                                                  ['name']].inputs[current_link['to_socket']['name']]
            output_socket = target.node_tree.nodes[current_link['from_node']
                                                   ['name']].outputs[current_link['from_socket']['name']]

            target.node_tree.links.new(input_socket, output_socket)
            print(data["node_tree"]["links"][link])

    except:
        print("Material loading error")


def load_gpencil(target=None, data=None, create=False):
    try:
        if target is None and create:
            bpy.data.grease_pencils.new(data["name"])

        if "layers" in data.keys():
            for layer in data["layers"]:
                print(layer)
        # Load other meshes metadata
        dump_anything.load(target, data)
    except:
        print("default loading error")


def load_light(target=None, data=None, create=False, type=None):
    try:
        if target is None and create:
            bpy.data.lights.new(data["name"],data["type"])

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


def update_scene(msg):
    global client

    if msg.id != client.id:
        net_vars = bpy.context.scene.session_settings

        if net_vars.active_object:
            if net_vars.active_object.name in msg.key:
                raise ValueError()

        if 'net' not in msg.key:
            target = resolve_bpy_path(msg.key)
            
            try:
                if msg.body["name"] in TASKS:
                    TASKS.remove(msg.body["name"])
            except:
                pass
            if msg.mtype == 'Object':
                load_object(target=target, data=msg.body,
                            create=net_vars.load_data)
            elif msg.mtype == 'Mesh':
                load_mesh(target=target, data=msg.body,
                            create=net_vars.load_data)
            elif msg.mtype == 'Collection':
                load_collection(target=target, data=msg.body,
                                create=net_vars.load_data)
            elif msg.mtype == 'Material':
                load_material(target=target, data=msg.body,
                                create=net_vars.load_data)
            elif msg.mtype == 'GreasePencil':
                load_gpencil(target=target, data=msg.body,
                                create=net_vars.load_data)
            elif msg.mtype == 'Scene':
                load_scene(target=target, data=msg.body,
                                create=net_vars.load_data)
            elif  'Light' in msg.mtype:
                load_light(target=target, data=msg.body,
                                create=net_vars.load_data)
            else:
                load_default(target=target, data=msg.body,
                                create=net_vars.load_data, type=msg.mtype)


recv_callbacks = [update_scene]
post_init_callbacks = [refresh_window]

     
# OPERATORS
class session_join(bpy.types.Operator):

    bl_idname = "session.join"
    bl_label = "join"
    bl_description = "connect to a net server"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client

        net_settings = context.scene.session_settings
        # Scene setup
        if net_settings.session_mode == "CONNECT" and net_settings.clear_scene:
            clean_scene()

        # Session setup
        if net_settings.username == "DefaultUser":
            net_settings.username = "{}_{}".format(
                net_settings.username, randomStringDigits())

        username = str(context.scene.session_settings.username)
        client_factory = rna_translation.RNAFactory()

        client = net_components.RCFClient(
            id=username,
            on_recv=recv_callbacks,
            on_post_init=post_init_callbacks,
            factory=client_factory,
            address=net_settings.ip,
            is_admin=net_settings.session_mode == "HOST")

        bpy.ops.asyncio.loop()

        net_settings.is_running = True

        bpy.ops.session.draw('INVOKE_DEFAULT')
        return {"FINISHED"}


class session_add_property(bpy.types.Operator):
    bl_idname = "session.add_prop"
    bl_label = "add"
    bl_description = "broadcast a property to connected clients"
    bl_options = {"REGISTER"}

    property_path: bpy.props.StringProperty(default="None")
    depth: bpy.props.IntProperty(default=1)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client

        item = resolve_bpy_path(self.property_path)

        print(item)

        if item:
            key = self.property_path

            dumper = dump_anything.Dumper()
            dumper.type_subset = dumper.match_subset_all
            dumper.depth = self.depth

            data = dumper.dump(item)
            data_type = item.__class__.__name__

            client.push_update(key, data_type, data)

        return {"FINISHED"}


class session_remove_property(bpy.types.Operator):
    bl_idname = "session.remove_prop"
    bl_label = "remove"
    bl_description = "broadcast a property to connected clients"
    bl_options = {"REGISTER"}

    property_path: bpy.props.StringProperty(default="None")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client

        try:
            del client.property_map[self.property_path]

            return {"FINISHED"}
        except:
            return {"CANCELED"}


class session_create(bpy.types.Operator):
    bl_idname = "session.create"
    bl_label = "create"
    bl_description = "create to a net session"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global server
        global client

        server = net_components.RCFServer()
        time.sleep(0.1)

        bpy.ops.session.join()

        if context.scene.session_settings.init_scene:
            init_scene()

        return {"FINISHED"}


class session_stop(bpy.types.Operator):
    bl_idname = "session.stop"
    bl_label = "close"
    bl_description = "stop net service"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global server
        global client

        net_settings = context.scene.session_settings

        if server:
            server.stop()
            del server
            server = None
        if client:
            client.stop()
            del client
            client = None
            bpy.ops.asyncio.stop()
            net_settings.is_running = False
        else:
            logger.debug("No server/client running.")

        return {"FINISHED"}


class session_settings(bpy.types.PropertyGroup):
    username = bpy.props.StringProperty(
        name="Username", default="user_{}".format(randomStringDigits()))
    ip = bpy.props.StringProperty(name="ip")
    port = bpy.props.IntProperty(name="5555")

    add_property_depth = bpy.props.IntProperty(
        name="add_property_depth", default=1)
    buffer = bpy.props.StringProperty(name="None")
    is_running = bpy.props.BoolProperty(name="is_running", default=False)
    load_data = bpy.props.BoolProperty(name="load_data", default=True)
    init_scene =  bpy.props.BoolProperty(name="load_data", default=True)
    clear_scene = bpy.props.BoolProperty(name="clear_scene", default=True)
    update_frequency = bpy.props.FloatProperty(
        name="update_frequency", default=0.008)
    active_object = bpy.props.PointerProperty(
        name="active_object", type=bpy.types.Object)
    session_mode = bpy.props.EnumProperty(
        name='session_mode',
        description='session mode',
        items={
            ('HOST', 'hosting', 'host a session'),
            ('CONNECT', 'connexion', 'connect to a session')},
        default='HOST')


class session_draw_clients(bpy.types.Operator):
    bl_idname = "session.draw"
    bl_label = "draw clients"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER"}

    position = bpy.props.FloatVectorProperty(default=(0, 0, 0))

    def __init__(self):
        super().__init__()

        self.draw_items = []
        self.draw3d_handle = None
        self.draw2d_handle = None
        self.draw_event = None
        self.coords = None
        self.active_object = None

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        #
        self.coords = None
        self.create_batch()
        self.register_handlers(context)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def register_handlers(self, context):
        self.draw3d_handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw3d_callback, (), 'WINDOW', 'POST_VIEW')
        self.draw2d_handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw2d_callback, (), 'WINDOW', 'POST_PIXEL')

        self.draw_event = context.window_manager.event_timer_add(
            0.008, window=context.window)

    def unregister_handlers(self, context):
        if self.draw_event and self.draw3d_handle and self.draw2d_handle:
            context.window_manager.event_timer_remove(self.draw_event)
            bpy.types.SpaceView3D.draw_handler_remove(
                self.draw3d_handle, "WINDOW")
            bpy.types.SpaceView3D.draw_handler_remove(
                self.draw2d_handle, "WINDOW")

            self.draw_items.clear()
            self.draw3d_handle = None
            self.draw2d_handle = None
            self.draw_event = None

    # TODO: refactor this ugly things
    def create_batch(self):
        global client
        index = 0
        index_object = 0
        for key, values in client.property_map.items():
            if values.body is not None:
                if values.mtype == "client_object":
                    if values.id != client.id and values.body is not None:
                        indices = (
                            (0, 1), (1, 2), (2, 3), (0, 3),
                            (4, 5), (5, 6), (6, 7), (4, 7),
                            (0, 4), (1, 5), (2, 6), (3, 7)
                        )

                        if values.body in bpy.data.objects.keys():
                            ob = bpy.data.objects[values.body]
                        else:
                            return
                        bbox_corners = [ob.matrix_world @ mathutils.Vector(corner) for corner in ob.bound_box]

                        coords = [(point.x, point.y, point.z)
                                  for point in bbox_corners]

                        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
                        batch = batch_for_shader(
                            shader, 'LINES', {"pos": coords}, indices=indices)

                        self.draw_items.append(
                            (shader, batch, (None, None), COLOR_TABLE[index-1]))

                    # index_object += 1

                if values.mtype == "client":
                    if values.id != client.id:
                        indices = (
                            (1, 3), (2, 1), (3, 0), (2, 0)
                        )

                        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
                        batch = batch_for_shader(
                            shader, 'LINES', {"pos": values.body}, indices=indices)

                        self.draw_items.append(
                            (shader, batch, (values.body[1], values.id.decode()), COLOR_TABLE[index]))
                    index += 1

    def draw3d_callback(self):

        bgl.glLineWidth(3)
        for shader, batch, font, color in self.draw_items:
            shader.bind()
            shader.uniform_float("color", color)
            batch.draw(shader)

    def draw2d_callback(self):
        for shader, batch, font, color in self.draw_items:
            try:
                coords = get_client_2d(font[0])

                blf.position(0, coords[0], coords[1]+10, 0)
                blf.size(0, 10, 72)
                blf.color(0, color[0], color[1], color[2], color[3])
                blf.draw(0,  font[1])

            except:
                pass

    def is_object_selected(self, obj):
        # TODO: function to find occurence
        global client

        for k, v in client.property_map.items():
            if v.mtype == 'client_object':
                if client.id != v.id:
                    if obj.name in v.body:
                        return True

        return False

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        if not context.scene.session_settings.is_running:
            self.finish(context)

        if event.type in {"TIMER"}:
            global client
            session = context.scene.session_settings

            if client:
                # Local view update
                current_coords = get_client_view_rect()
                if current_coords != self.coords:
                    self.coords = current_coords
                    key = "net/clients/{}".format(client.id.decode())

                    client.push_update(key, 'client', current_coords)

                # Hide selected objects
                for object in context.scene.objects:
                    if self.is_object_selected(object):
                        object.hide_select = True
                    else:
                        object.hide_select = False

                # Active object bounding box
                if len(context.selected_objects) > 0:
                    if session.active_object is not context.selected_objects[0] or session.active_object.is_evaluated:
                        session.active_object = context.selected_objects[0]
                        key = "net/objects/{}".format(client.id.decode())
                        client.push_update(
                            key, 'client_object', session.active_object.name)

                elif len(context.selected_objects) == 0 and session.active_object:
                    session.active_object = None
                    key = "net/objects/{}".format(client.id.decode())
                    client.push_update(key, 'client_object', None)

                # Draw clients
                if len(client.property_map) > 0:
                    self.unregister_handlers(context)
                    self.create_batch()

                    self.register_handlers(context)

        return {"PASS_THROUGH"}

    def finish(self, context):
        self.unregister_handlers(context)
        return {"FINISHED"}


class session_snapview(bpy.types.Operator):
    bl_idname = "session.snapview"
    bl_label = "draw clients"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER"}

    target_client = bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client

        area, region, rv3d = view3d_find()

        for k, v in client.property_map.items():
            if v.mtype == 'client' and v.id.decode() == self.target_client:
                rv3d.view_location = v.body[1]
                rv3d.view_distance = 30.0
                return {"FINISHED"}

        return {"CANCELLED"}

        pass


# TODO: Rename to match official blender convention
classes = (
    session_join,
    session_add_property,
    session_stop,
    session_create,
    session_settings,
    session_remove_property,
    session_draw_clients,
    session_snapview,
)

def update_loop():
    for t in TASKS:
        dump_datablock(bpy.data.objects[t].data,4)
        dump_datablock(bpy.data.objects[t],1)
        dump_datablock(bpy.data.scenes[0],4)

    return 0.5

    
def depsgraph_update(scene):
    for c in bpy.context.depsgraph.updates.items():
        global client
        if client:
            if client.status == net_components.RCFStatus.CONNECTED:
                if c[1].is_updated_geometry:
                    print("GEOMETRY UPDATE")
                elif c[1].is_updated_transform:
                    print("TRANFORM UPDATE")
                    dump_datablock_attibute(bpy.data.objects[c[1].id.name],['matrix_world'])
                else:
                    data_name = c[1].id.name
                    if data_name in bpy.data.objects.keys():
                        found = False
                        for k in client.property_map.keys():
                            if  data_name in k:
                                found = True
                                break

                        if not found:
                            client.property_map["Object/{}".format(data_name)] = net_components.RCFMessage("Object/{}".format(data_name), "Object", None)
                            upload_mesh(bpy.data.objects[data_name].data)
                            dump_datablock(bpy.data.objects[data_name],1)
                            dump_datablock(bpy.data.scenes[0],4)                
                            
                            # dump_datablock(bpy.data.scenes[0],4)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.session_settings = bpy.props.PointerProperty(
        type=session_settings)
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update)
    bpy.app.timers.register(update_loop)

def unregister():
    global server
    global client

    try:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update)
        bpy.app.timers.unregister(update_loop)
    except:
        pass

    if server:
        server.stop()
        del server
        server = None
    if client:
        client.stop()
        del client
        client = None

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    
    del bpy.types.Scene.session_settings
    

if __name__ == "__main__":
    register()
