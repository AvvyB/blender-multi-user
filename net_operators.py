import bpy
from . import net_components
import time
import logging
import mathutils

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

VECTOR_TYPES = (
    'Vector'
)

# TODO: Less ugly method
def from_bpy(value):
    logger.debug(' casting from bpy')
    value_type = type(value)
    value_casted = None

    if value_type is mathutils.Vector:
        value_casted =  [value.x,value.y,value.z]
    elif value_type is bpy.props.collection:
        pass # TODO: Collection replication
    elif value_type is mathutils.Euler:
        value_casted =  [value.x,value.y,value.z]
    elif value_type is NATIVE_TYPES:
        value_casted = value
    
    return str(value.__class__.__name__),value_casted

def to_bpy(store_item):
    """
    Get bpy value from store
    """
    value_type = store_item.mtype
    value_casted = None
    store_value = store_item.body

    if value_type == 'Vector':
        value_casted = mathutils.Vector((store_value[0],store_value[1],store_value[2]))

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
        obj = getattr(bpy.data,path[0])[path[1]]
        attribute = getattr(obj,path[2])
        logger.debug("done {} : {}".format(obj,attribute))
    except AttributeError:
        logger.debug(" Attribute not found")

    return obj, attribute

def observer():
    global client

    try:
        for key,values in client.property_map.items():
            # if values.id == client.id:
            obj, attr = resolve_bpy_path(key)

            if attr != to_bpy(client.property_map[key]):
                value_type, value = from_bpy(attr)
                client.push_update(key,value_type,value)
    except:
        pass
        
    return 0.16


# CLIENT-SERVER
def refresh_window(msg):
    import bpy

    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

def patch_scene(msg):
    global client

    if msg.id != client.id:
        value = None

        obj, attr = resolve_bpy_path(msg.key)
        attr_name = msg.key.split('/')[2] 

        value  = to_bpy(msg)
        
        logger.debug("Updating scene:\n object: {} attribute: {} , value: {}".format(obj, attr_name, value))
    
        try:
            setattr(obj,attr_name,value)
        except:
            pass
    else:
        logger.debug('no need to update scene on our own')

def vector2array(v):
    return [v.x,v.y,v.z]

def array2vector(a):
    logger.debug(mathutils.Vector((a[0],a[1],a[2])))
    return mathutils.Vector((a[0],a[1],a[2]))

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

        username = str(context.scene.session_settings.username)
        callbacks=[patch_scene]

        client = net_components.Client(id=username,recv_callback=callbacks)
        time.sleep(1)

        bpy.ops.asyncio.loop()
        bpy.app.timers.register(observer)

        return {"FINISHED"}


class session_send(bpy.types.Operator):
    bl_idname = "session.send"
    bl_label = "send"
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
            
            client.push_update(key,value_type,value)

        return {"FINISHED"}

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

        username = str(context.scene.session_settings.username)
        callbacks=[patch_scene]

        server = net_components.Server()
        client = net_components.Client(id=username,recv_callback=callbacks)

        # time.sleep(0.1)

        bpy.ops.asyncio.loop()
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

        if server :
            server.stop()
            del server
            server = None
        if client:
            client.stop()
            del client
            client = None
            bpy.ops.asyncio.stop()
        else:
            logger.debug("No server/client running.")

        return {"FINISHED"}


class session_settings(bpy.types.PropertyGroup):
    username = bpy.props.StringProperty(name="Username",default="DefaultUser")
    ip = bpy.props.StringProperty(name="localhost")
    port = bpy.props.IntProperty(name="5555")
    buffer = bpy.props.StringProperty(name="None")

# TODO: Rename to match official blender convention
classes = (
    session_join,
    session_send,
    session_stop,
    session_create,
    session_settings,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.session_settings = bpy.props.PointerProperty(type=session_settings)
    # bpy.app.handlers.depsgraph_update_post.append(observer)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.session_settings


if __name__ == "__main__":
    register()
