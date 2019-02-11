import bpy
from . import net_components
import time

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

class client_connect(bpy.types.Operator):
    bl_idname = "client.connect"
    bl_label = "connect"
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

class server_connect(bpy.types.Operator):
    bl_idname = "server.run"
    bl_label = "connect"
    bl_description = "connect to a net server"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global server
        
        server = net_components.Server()
        
        time.sleep(1)
        
        bpy.ops.asyncio.loop()
        

        return {"FINISHED"}

classes = (
    join,
    create,
    close,
    send,
    client_connect,
    server_connect,
)


def register():
    global session
    # session = net_components.Session()
    

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
