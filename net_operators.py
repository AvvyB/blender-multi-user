import bpy
from . import net_components
from . import rna_translation
import time
import logging
import mathutils
import random
import string
import gpu
from gpu_extras.batch import batch_for_shader

logger = logging.getLogger(__name__)

client = None
server = None
context = None

NATIVE_TYPES = (
    bpy.types.IntProperty,
    bpy.types.FloatProperty,
    bpy.types.BoolProperty,
    bpy.types.StringProperty,
)


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
    logger.debug(' casting from bpy')
    value_type = type(value)
    value_casted = None

    if value_type is mathutils.Vector:
        value_casted = [value.x, value.y, value.z]
    elif value_type is bpy.props.collection:
        pass  # TODO: Collection replication
    elif value_type is mathutils.Euler:
        value_casted = [value.x, value.y, value.z]
    elif value_type is NATIVE_TYPES:
        value_casted = value

    return str(value.__class__.__name__), value_casted


def to_bpy(store_item):
    """
    Get bpy value from store
    """
    value_type = store_item.mtype
    value_casted = None
    store_value = store_item.body

    if value_type == 'Vector':
        value_casted = mathutils.Vector(
            (store_value[0], store_value[1], store_value[2]))

    return value_casted


def resolve_bpy_path(path):
    """
    Get bpy property value from path
    """

    path = path.split('/')

    obj = None
    attribute = path[2]
    logger.debug("resolving {}".format(path))

    try:
        obj = getattr(bpy.data, path[0])[path[1]]
        attribute = getattr(obj, path[2])
        logger.debug("done {} : {}".format(obj, attribute))
    except AttributeError:
        logger.debug(" Attribute not found")

    return obj, attribute


def observer():
    global client

   
    for key, values in client.property_map.items():
        if client.id in key:
            #client position update 
            pass
        else:
            try:
                obj, attr = resolve_bpy_path(key)

                if attr != to_bpy(client.property_map[key]):
                    value_type, value = from_bpy(attr)
                    client.push_update(key, value_type, value)
            except:
                pass

    return bpy.context.scene.session_settings.update_frequency

def refresh_window():
    import bpy

    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

def init_scene(msg):
    pass

def update_scene(msg):
    global client

    if msg.id != client.id:
        value = None

        obj, attr = resolve_bpy_path(msg.key)
        attr_name = msg.key.split('/')[2]

        value = to_bpy(msg)
        # print(msg.get)
        logger.debug("Updating scene:\n object: {} attribute: {} , value: {}".format(
            obj, attr_name, value))
        try:
            setattr(obj, attr_name, value)
        except:
            pass
    else:
        logger.debug('no need to update scene on our own')

def update_ui(msg):
    """
    Update collaborative UI elements
    """
    pass

recv_callbacks = [update_scene,update_ui]
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
            factory=client_factory)
        # time.sleep(1)

        bpy.ops.asyncio.loop()
        bpy.app.timers.register(observer)


        net_settings.is_running = True
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

        obj, attr = resolve_bpy_path(self.property_path)

        if obj and attr:
            key = self.property_path
            value_type, value = from_bpy(attr)

            client.push_update(key, value_type, value)

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

        if server:
            server.stop()
            del server
            server = None
        if client:
            client.stop()
            del client
            client = None
            bpy.ops.asyncio.stop()

            bpy.app.timers.unregister(observer)
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
    update_frequency = bpy.props.FloatProperty(
        name="update_frequency", default=0.008)


# TODO: Rename to match official blender convention
classes = (
    session_join,
    session_add_property,
    session_stop,
    session_create,
    session_settings,
    session_remove_property,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.session_settings = bpy.props.PointerProperty(
        type=session_settings)

    # bpy.app.handlers.depsgraph_update_post.append(on_scene_evalutation)


def unregister():

    global server
    global client

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

    # bpy.app.handlers.depsgraph_update_post.remove(on_scene_evalutation)

    del bpy.types.Scene.session_settings


if __name__ == "__main__":
    register()
