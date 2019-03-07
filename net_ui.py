import bpy
from . import net_components
from . import net_operators
import gpu
from gpu_extras.batch import batch_for_shader

class DrawClient(bpy.types.Operator):
    bl_idname = "session.draw"
    bl_label = "DrawClient"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER"}

    coords = (
    (-1, -1, -1), (+1, -1, -1),
    (-1, +1, -1), (+1, +1, -1),
    (-1, -1, +1), (+1, -1, +1),
    (-1, +1, +1), (+1, +1, +1))

    indices = (
        (0, 1), (0, 2), (1, 3), (2, 3),
        (4, 5), (4, 6), (5, 7), (6, 7),
        (0, 4), (1, 5), (2, 6), (3, 7))
    def __init__(self):
        super().__init__()

        self.shader = None
        self.batch = None 
        self.draw_handle = None

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context,event):
        self.create_batch()

        self.register_handlers()

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def register_handlers(self):
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (), 'WINDOW', 'POST_VIEW')

    def unregister_handlers(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle,"WINDOW")

    def create_batch(self):
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.batch = batch_for_shader(self.shader, 'LINES', {"pos": self.coords}, indices=self.indices)

    def draw_callback(self):
        self.shader.bind()
        self.shader.uniform_float("color", (1, 0, 0, 1))
        self.batch.draw(self.shader)

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()
        
        if event.type in {"ESC"}:
            self.unregister_handlers()
            return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def finish(self):
        self.unregister_handlers()
        return {"FINISHED"}


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
        row.operator("session.draw")
classes = (
    DrawClient,
    SessionPanel,
)


register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()