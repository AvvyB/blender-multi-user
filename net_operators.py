import bpy
from . import net_components
import time
import logging
import mathutils

logger = logging.getLogger(__name__)

client = None
server = None
context = None


# CLIENT-SERVER
def refresh_window(msg):
    import bpy

    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

def patch_scene(msg):
    path = msg.key.split('/')

    attribute = getattr(getattr(bpy.data,path[0])[path[1]],path[2])
    print(type(attribute))
    if type(attribute) == mathutils.Vector:
        attribute = array2vector(msg.body)

def vector2array(v):
    return [v.x,v.y,v.z]

def array2vector(a):
    print(mathutils.Vector((a[0],a[1],a[2])))
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
        callbacks=[refresh_window,patch_scene]

        client = net_components.Client(id=username  ,recv_callback=callbacks)
        time.sleep(1)

        bpy.ops.asyncio.loop()

        return {"FINISHED"}


class session_send(bpy.types.Operator):
    bl_idname = "session.send"
    bl_label = "send"
    bl_description = "broadcast a message to connected clients"
    bl_options = {"REGISTER"}

    message: bpy.props.StringProperty(default="Hi")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client

        key = "objects/Cube/location"
        value = vector2array(bpy.data.objects['Cube'].location)

        client.push_update(key,value)

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
        callbacks=[refresh_window,patch_scene]

        server = net_components.Server()
        client = net_components.Client(id=username,recv_callback=callbacks)

        time.sleep(1)

        bpy.ops.asyncio.loop()

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
            logger.info("No server/client running.")

        return {"FINISHED"}


class session_settings(bpy.types.PropertyGroup):
    username = bpy.props.StringProperty(name="Username",default="DefaultUser")
    ip = bpy.props.StringProperty(name="localhost")
    port = bpy.props.IntProperty(name="5555")

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

def unregister():    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    del bpy.types.Scene.session_settings


if __name__ == "__main__":
    register()
