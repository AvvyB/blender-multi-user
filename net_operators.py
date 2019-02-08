import bpy
from . import net_components

session = None


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


classes = (
    join,
    create,
    close,
    send,
)


def register():
    global session
    session = net_components.Session()

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
