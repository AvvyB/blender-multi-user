from bpy_extras import view3d_utils
import bpy
from . import net_components
from . import net_ui
from . import rna_translation
from .libs import dump_anything
import time
import logging
import mathutils
import random
import string
import bgl
import blf
import gpu
from gpu_extras.batch import batch_for_shader

logger = logging.getLogger(__name__)

client = None
server = None
context = None

SUPPORTED_DATABLOCKS = ['objects']

REPLICATED_PROPERTIES = ['matrix_world']
# 'actions','armatures','cameras','collections','curves','grease_pencils','images','materials','materials',,'scenes','textures'
COLOR_TABLE = [(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1),
               (0, 0.5, 1, 1), (0.5, 0, 1, 1)]
NATIVE_TYPES = (
    int,
    float,
    bool,
    string,
)


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


def on_scene_evalutation(scene):
    # TODO: viewer representation
    # TODO: Live update only selected object
    # TODO: Scene representation
    pass


def randomStringDigits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


def match_supported_types(value):
    type_factory = None

    if isinstance(value, bool):
        print("float")
    elif isinstance(value, mathutils.Vector):
        print("vector")
        type_factory = VectorTypeTranslation()
    elif isinstance(value, mathutils.Euler):
        print("Euler")
    elif type(value) in NATIVE_TYPES:
        print("native")
    else:
        raise NotImplementedError

    return type_factory


# TODO: Less ugly method
def from_bpy(value):
    # logger.debug(' casting from bpy')
    value_type = type(value)
    value_casted = None

    if value_type is mathutils.Vector or value_type is mathutils.Euler:
        value_casted = [value.x, value.y, value.z]
    elif isinstance(value,mathutils.Matrix):
        value_casted = []
        for r in value.row:
            value_casted.extend([r[0], r[1], r[2],r[3]])
    elif value_type is bpy.props.collection:
        pass  # TODO: Collection replication
    # elif value_type is mathutils.Euler:
    #     value_casted = [value.x, value.y, value.z]
    elif value_type in NATIVE_TYPES:
        value_casted = value

    return str(value.__class__.__name__), value_casted


def to_bpy(store_item):
    """
    Get bpy value from store
    """
    value_type = store_item.mtype
    value_casted = None
    store_value = store_item.body

    if value_type == 'Vector' or 'Euler':
        value_casted = mathutils.Vector(
            (store_value[0], store_value[1], store_value[2]))
    if value_type == 'Matrix':
        mat = mathutils.Matrix()
        mat[0] = mathutils.Vector((store_value[0], store_value[1], store_value[2], store_value[3]))
        mat[1] = mathutils.Vector((store_value[4], store_value[5], store_value[6], store_value[7]))
        mat[2] = mathutils.Vector((store_value[8], store_value[9], store_value[10], store_value[11]))
        mat[3] = mathutils.Vector((store_value[12], store_value[13], store_value[14], store_value[15]))
        value_casted = mat
    return value_casted


def resolve_bpy_path(path):
    """
    Get bpy property value from path
    """
    path = path.split('/')
    item = None

    try:
        item = getattr(bpy.data, path[0])[path[1]]

    except AttributeError:
        pass

    return item

def observer(scene):
    global client
    pass
    # if client:
    #     for key, values in client.property_map.items():
    #         try:
    #             obj, attr = resolve_bpy_path(key)

    #             if attr != to_bpy(client.property_map[key]):
    #                 value_type, value = from_bpy(attr)
    #                 client.push_update(key, value_type, value)
    #         except:
    #             pass

    return bpy.context.scene.session_settings.update_frequency


def mark_objects_for_update(scene):
    for item in dir(bpy.data):
        if item in SUPPORTED_DATABLOCKS:
            for datablock in getattr(bpy.data,item):
                if bpy.context.object.is_evaluated:
                    print("EVALUATED: {}:{}".format(item,datablock.name))
                
 
def refresh_window():
    import bpy
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)


def init_scene():
    global client
    

def update_scene(msg):
    global client

    if msg.id != client.id:
        # try:
        value = None
        if bpy.context.scene.session_settings.active_object:
            if bpy.context.scene.session_settings.active_object.name in msg.key:
                raise ValueError()

        item =  resolve_bpy_path(msg.key)
        
        if item:
            loader = dump_anything.Loader()
            loader.load(item, msg.body)
        
        # print(msg.get)
        # logger.debug("Updating scene:\n object: {} attribute: {} , value: {}".format(
        # obj, attr_name, value))

        # setattr(obj, attr_name, value)
        # except:
        #     pass
    else:
        pass
        # logger.debug('no need to update scene on our own')


def update_ui(msg):
    """
    Update collaborative UI elements
    """
    pass


recv_callbacks = [update_scene, update_ui]
post_init_callbacks = [refresh_window]


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

        if net_settings.username == "DefaultUser":
            net_settings.username = "{}_{}".format(
                net_settings.username, randomStringDigits())

        username = str(context.scene.session_settings.username)

        client_factory = rna_translation.RNAFactory()
        print("{}".format(client_factory.__class__.__name__))
        client = net_components.Client(
            id=username,
            on_recv=recv_callbacks,
            on_post_init=post_init_callbacks,
            factory=client_factory,
            address=net_settings.ip)
        # time.sleep(1)

        bpy.ops.asyncio.loop()
        # bpy.app.timers.register(observer)

        net_settings.is_running = True

        # bpy.ops.session.draw('INVOKE_DEFAULT')
        return {"FINISHED"}


class session_add_property(bpy.types.Operator):
    bl_idname = "session.add_prop"
    bl_label = "add"
    bl_description = "broadcast a property to connected clients"
    bl_options = {"REGISTER"}

    property_path: bpy.props.StringProperty(default="None")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client

        item = resolve_bpy_path(self.property_path)

        print(item)

        if item :
            key = self.property_path

            dumper = dump_anything.Dumper()
            dumper.type_subset = dumper.match_subset_all
            dumper.depth = 3

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

        server = net_components.Server()
        time.sleep(0.1)

        bpy.ops.session.join()

        # init_scene()

        bpy.app.timers.register(observer)
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

        # bpy.app.timers.unregister(observer)

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
    ip = bpy.props.StringProperty(name="localhost")
    port = bpy.props.IntProperty(name="5555")
    buffer = bpy.props.StringProperty(name="None")
    is_running = bpy.props.BoolProperty(name="is_running", default=False)
    hide_users = bpy.props.BoolProperty(name="is_running", default=False)
    hide_settings = bpy.props.BoolProperty(name="hide_settings", default=False)
    hide_properties = bpy.props.BoolProperty(
        name="hide_properties", default=True)
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
                if values.mtype == "object":
                    if values.id != client.id:
                        indices = (
                            (0, 1), (1, 2), (2, 3), (0, 3),
                            (4, 5), (5, 6), (6, 7), (4, 7),
                            (0, 4), (1, 5), (2, 6), (3, 7)
                        )

                        ob = bpy.data.objects[values.body]

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
            if v.mtype == 'object':
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
                            key, 'object', session.active_object.name)

                elif len(context.selected_objects) == 0 and session.active_object:
                    session.active_object = None
                    key = "net/objects/{}".format(client.id.decode())
                    client.push_update(key, 'object', None)

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

class load_data(bpy.types.Operator):
    bl_idname = "session.load_data"
    bl_label = "Get bpy data"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER","UNDO"}

    @classmethod
    def poll(cls, context):
        return True
 
    def explore(self, root):
        for item in root.bl_rna.properties:
            if item.name not in ['RNA']:
                
                print((item.name))
                # self.explore(item)
            
    def execute(self, context):
        obj = bpy.data.meshes['Cube']

        dumper = dump_anything.Dumper()
        dumper.type_subset = dumper.match_subset_all
        dumper.depth = 3

        c = dumper.dump(obj)
        # bpy.data.meshes.remove(obj)
        import json
        with open('test.json', 'w+') as outfile:
            json.dump(c, outfile, indent=4)

        # newo = bpy.data.meshes.new(c["name"])
        # print(c)
        # loader = dump_anything.Loader()
        # loader.load(c, newo)
        # bpy.data.collections['Collection'].objects.link(newo)
        # self.explore(bpy.data.objects)
                # for datablock in getattr(bpy.data,item):
                #     print(": {}:{}".format(item,datablock.name))
        return {"FINISHED"}


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
    load_data,
)

def depsgraph_update(scene):
    for c in bpy.context.depsgraph.updates.items():
        # print(c[1].id)
        if c[1].is_updated_geometry:
            pass
        if c[1].is_updated_transform:
            pass

            # print(dumper.dump(c[1]))


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.session_settings = bpy.props.PointerProperty(
        type=session_settings)

    # bpy.app.handlers.depsgraph_update_post.append(depsgraph_update)
    # bpy.app.handlers.depsgraph_update_post.append(observer)


def unregister():
    try:
        bpy.app.handlers.depsgraph_update_post.remove(observer)
    except:
        pass
    global server
    global client

    # bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update)
    # bpy.app.handlers.depsgraph_update_post.remove(observer)
    # bpy.app.handlers.depsgraph_update_post.remove(mark_objects_for_update)

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
