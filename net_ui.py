import bpy
from . import net_components
from . import net_operators
import mathutils
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils

def view3d_find():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    return area, region, rv3d
                    
                    break
    return None, None, None

def get_target(region, rv3d,coord):
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    return  ray_origin +view_vector

def get_client_view_rect():
    area, region, rv3d = view3d_find()

    width = region.width
    height = region.height

    v1 = get_target(region,rv3d,(0,0))
    v3 = get_target(region,rv3d,(0,height))
    v2 = get_target(region,rv3d,(width,height))
    v4 = get_target(region,rv3d,(width,0))

    coords = (v1, v2, v3, v4)
    indices = (
            (1, 3), (2, 1), (3, 0),(2,0)
    )

class DrawClient(bpy.types.Operator):
    bl_idname = "session.draw"
    bl_label = "DrawClient"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER"}

    position = bpy.props.FloatVectorProperty(default=(0,0,0))
    def __init__(self):
        super().__init__()

        self.shader = None
        self.batch = None 
        self.draw_handle = None
        self.draw_event = None
        self.coords = None
        self.indices = None

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context,event):
        try:
            self.unregister_handlers()
        except:
            pass

        area, region, rv3d = view3d_find()
        width = region.width
        height = region.height
        depth = mathutils.Vector((rv3d.view_distance,rv3d.view_distance,rv3d.view_distance))
        vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, (0,0))
        
        v1 = get_target(region,rv3d,(0,0))
        v3 = get_target(region,rv3d,(0,height))
        v2 = get_target(region,rv3d,(width,height))
        v4 = get_target(region,rv3d,(width,0))

        print("{}".format(rv3d.view_distance))
        self.coords = (v1, v2, v3, v4)


        self.indices = (
             (1, 3), (2, 1), (3, 0),(2,0)
        )

        self.create_batch()

        self.register_handlers(context)

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def register_handlers(self,context):
        self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (), 'WINDOW', 'POST_VIEW')
        self.draw_event = context.window_manager.event_timer_add(0.1, window=context.window)

    def unregister_handlers(self,context):
        context.window_manager.event_timer_remove(self.draw_event)
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle,"WINDOW")

        self.draw_handle = None
        self.draw_event = None

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
            self.unregister_handlers(context)
            return {"CANCELLED"}
        # if self.draw_handle:
        #     self.finish()

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