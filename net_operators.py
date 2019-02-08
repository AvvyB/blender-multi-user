import bpy
from . import net_components

session = None

class join(bpy.types.Operator):
    bl_idname = "session.join"
    bl_label = "connect to net session"
    bl_description = "Connect to a net session"
    bl_options = {"REGISTER"}


    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global session

        session = net_components.Session()
        bpy.ops.asyncio.loop()
        return {"FINISHED"}

class host(bpy.types.Operator):
    bl_idname = "session.host"
    bl_label = "host a net session"
    bl_description = "Connect to a net session"
    bl_options = {"REGISTER"}


    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global session

        session = net_components.Session(is_hosting=True)
        bpy.ops.asyncio.loop()
        return {"FINISHED"}

class send(bpy.types.Operator):
    bl_idname = "session.send"
    bl_label = "Send a message throught the network"
    bl_description = "Connect to a net session"
    bl_options = {"REGISTER"}

    message: bpy.props.StringProperty(default="Hi")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global session

        session.send(b"")
        return {"FINISHED"}

class close(bpy.types.Operator):
    bl_idname = "session.close"
    bl_label = "Send a message throught the network"
    bl_description = "Connect to a net session"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global session

        bpy.ops.asyncio.stop()
        session.close()

        return {"FINISHED"}

classes = (
    join,
    host,
    send
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()