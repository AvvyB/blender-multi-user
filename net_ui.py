import bpy
from . import net_components
from . import net_operators

class SessionPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Net Session"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    # def draw_header(self, context):
    #     self.layout.prop(context.scene, "use_gravity", text="")

    def draw(self, context):
        layout = self.layout
        global session

        scene = context.scene
        # Create a simple row.
        row = layout.row()

        if not session:
            row.operator("session.join")
            row.operator("session.host")
        else:
            row.operator("session.close")
        
        # row.operator("session.send").message = bpy.scene.message
        # row.prop(scene,"message")
    

classes = (
    SessionPanel,
)


register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()