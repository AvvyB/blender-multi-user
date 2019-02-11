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
        
        scene = context.scene
        # Create a simple row.
        row = layout.row()

        if net_operators.session.is_running:
            row.operator("session.close")
            row = layout.row()

            row = layout.row(align=True)
            row.prop(scene,"message",text="")
            row.operator("session.send").message = scene.message
            row = layout.row()
            # Debug area 

            row.label(text="Debug")

            row = layout.row()
            area_msg = row.box()
            if len(net_operators.session.msg) > 0:
                for msg in net_operators.session.msg:
                    area_msg.label(text=str(msg))
            else:
                area_msg.label(text="Empty")
        else:
            row.operator("session.join")
            row.operator("session.create")
        
       
    
        

classes = (
    # SessionPanel,
)


register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()