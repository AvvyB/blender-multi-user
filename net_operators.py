import bpy
from . import net_components
import time
import logging

logger = logging.getLogger(__name__)

session = None
client = None
server = None
context = None

# SESSION Operators


class join(bpy.types.Operator):
    bl_idname = "session.join"
    bl_label = "join"
    bl_description = "Connect to a net session"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        # global session

        if session.join():
            bpy.ops.asyncio.loop()
        else:
            print('fail to create session, avorting loop')
        return {"FINISHED"}


class create(bpy.types.Operator):
    bl_idname = "session.create"
    bl_label = "create"
    bl_description = "create to a net session"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global session

        if session.create():
            bpy.ops.asyncio.loop()
        else:
            print('fail to create session, avorting loop')

        return {"FINISHED"}


class send(bpy.types.Operator):
    bl_idname = "session.send"
    bl_label = "Send"
    bl_description = "Connect to a net session"
    bl_options = {"REGISTER"}

    message: bpy.props.StringProperty(default="Hi")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global session

        session.send(self.message)
        return {"FINISHED"}


class close(bpy.types.Operator):
    bl_idname = "session.close"
    bl_label = "Close session"
    bl_description = "Connect to a net session"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global session

        session.close()
        bpy.ops.asyncio.stop()
        return {"FINISHED"}

# CLIENT-SERVER


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

        client = net_components.Client()
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

        client.send_msg(self.message)

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

        server = net_components.Server()
        client = net_components.Client()

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


classes = (
    session_join,
    session_send,
    session_stop,
    session_create,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
