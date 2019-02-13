import bpy
from . import net_components
from . import net_operators

class SessionPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "RFC Session"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    # def draw_header(self, context):
    #     self.layout.prop(context.scene.session_settings, "username", text="")

    def draw(self, context):
        layout = self.layout
        
        scene = context.scene
        # Create a simple row.
        row = layout.row()

        if net_operators.client:
            row.operator("session.stop")
            row = layout.row()

            row = layout.row(align=True)

            row.operator("session.send")
            row = layout.row()
            # Debug area 

            row = layout.row()
            area_msg = row.box()
            if len(net_operators.client.property_map) > 0:
                for key,value in net_operators.client.property_map.items():
                    area_msg.label(text="{}:{}".format(key,value))
            else:
                area_msg.label(text="Empty")
            
        else:
            row = layout.row()
            row.prop(scene.session_settings,"username",text="")
            row = layout.row()
            row.operator("session.join")
            row.operator("session.create")
        
       



classes = (
    SessionPanel,
)


register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()