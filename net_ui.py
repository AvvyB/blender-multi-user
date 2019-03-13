import bpy
from . import net_components
from . import net_operators


class SessionPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "bl network"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw_header(self, context):
        net_settings = context.scene.session_settings

        if net_settings.is_running:
            self.layout.label(text="",icon='HIDE_OFF')
        else:
            self.layout.label(text="",icon='HIDE_ON')
            # self.layout.label(text="Offline")

    def draw(self, context):
        layout = self.layout
        
        net_settings = context.scene.session_settings
        scene = context.scene
        # Create a simple row.
        row = layout.row()

        if net_operators.client:
            row.label(text="Net frequency:")
            row.prop(net_settings,"update_frequency",text="")
            row = layout.row(align=True)
            row.prop(net_settings,"buffer", text="")
            row.operator("session.add_prop", text="",icon="ADD").property_path = net_settings.buffer
            row = layout.row()
            # Debug area 

            row = layout.row()  
            area_msg = row.box()
            if len(net_operators.client.property_map) > 0:  
                for key,values in net_operators.client.property_map.items():
                    item_box = area_msg.box()
                    detail_item_box = item_box.row()
                    # detail_item_box = item_box.row()
                    detail_item_box.label(text="{} ({}) ".format(key, values.mtype, values.id.decode()))
                    detail_item_box.operator("session.remove_prop",text="",icon="X").property_path = key
            else:
                area_msg.label(text="Empty")
            
            row = layout.row()
            row.operator("session.stop")
            
        else:
            row = layout.row()
            row.prop(scene.session_settings,"username",text="username:")
            row = layout.row()
            row.operator("session.join")
            row = layout.row()
            row.operator("session.create")

        row = layout.row()
        # row.operator("session.draw")
        # row.operator("session.update_client")
classes = (
    SessionPanel,
)


register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()