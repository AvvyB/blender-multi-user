import bpy
from . import operators
from .libs.replication.constants import *


ICONS = {'Image': 'IMAGE_DATA', 'Curve':'CURVE_DATA', 'Client':'SOLO_ON','Collection': 'FILE_FOLDER', 'Mesh': 'MESH_DATA', 'Object': 'OBJECT_DATA', 'Material': 'MATERIAL_DATA',
                  'Texture': 'TEXTURE_DATA', 'Scene': 'SCENE_DATA','AreaLight':'LIGHT_DATA', 'Light': 'LIGHT_DATA', 'SpotLight': 'LIGHT_DATA', 'SunLight': 'LIGHT_DATA', 'PointLight': 'LIGHT_DATA', 'Camera': 'CAMERA_DATA', 'Action': 'ACTION', 'Armature': 'ARMATURE_DATA', 'GreasePencil': 'GREASEPENCIL'}

PROP_STATES = [ 'ADDED',
                'COMMITED',
                'PUSHED',
                'FETCHED',
                'UP']
class SESSION_PT_settings(bpy.types.Panel):
    """Settings panel"""
    bl_idname = "MULTIUSER_SETTINGS_PT_panel"
    bl_label = "Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"

    def draw_header(self, context):
        self.layout.label(text="", icon='TOOL_SETTINGS')


    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if hasattr(context.window_manager, 'session'):
            settings = context.window_manager.session
            window_manager = context.window_manager

            # STATE INITIAL
            if not operators.client or (operators.client and operators.client.state == 0):
                pass
                # REPLICATION SETTINGS
                # row = layout.row()
                # box = row.box()
                # row = box.row()
                # row.label(text="REPLICATION", icon='TRIA_RIGHT')
                # row = box.row()    
                
                # for item in window_manager.session.supported_datablock:
                #     row.label(text=item.type_name,icon=ICONS[item.type_name])
                #     row.prop(item, "is_replicated", text="") 
                #     row = box.row()
            else:
                 # STATE ACTIVE
                if operators.client.state ==  2:
                    
                    row = layout.row()
                    row.operator("session.stop", icon='QUIT', text="Exit")
                    row = layout.row()

                # STATE SYNCING
                else:    
                    status = "connecting..."
                    row.label(text=status)
                    row = layout.row()
                    row.operator("session.stop", icon='QUIT', text="CANCEL")



class SESSION_PT_settings_network(bpy.types.Panel):
    bl_idname = "MULTIUSER_SETTINGS_NETWORK_PT_panel"
    bl_label = "Network"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'
    @classmethod
    def poll(cls, context):
        return  not operators.client or (operators.client and operators.client.state == 0)
    
    def draw(self, context):
        layout = self.layout

        settings = context.window_manager.session
        scene = context.window_manager
        row = layout.row()
        # USER SETTINGS
        row.label(text="draw overlay:")
        row.prop(settings, "enable_presence", text="")
        row = layout.row()
        row.label(text="clear blend:")
        row.prop(settings, "start_empty", text="")
        row = layout.row()
    
        row = layout.row()
        row.prop(settings, "session_mode", expand=True)
        row = layout.row()

        if settings.session_mode == 'HOST':
            box = row.box()
            row = box.row()
            row.label(text="init scene:")
            row.prop(settings, "init_scene", text="")
            row = box.row()
            row.operator("session.start", text="HOST").host = True
        else:
            box = row.box()
            row = box.row()
            row.prop(settings, "ip", text="ip")
            row = box.row()
            row.label(text="port:")
            row.prop(settings, "port", text="")
            row = box.row()
            

            row = box.row()
            row.operator("session.start", text="CONNECT").host = False


class SESSION_PT_settings_user(bpy.types.Panel):
    bl_idname = "MULTIUSER_SETTINGS_USER_PT_panel"
    bl_label = "User"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'
    @classmethod
    def poll(cls, context):
        return  not operators.client or (operators.client and operators.client.state == 0)
    
    def draw(self, context):
        layout = self.layout

        settings = context.window_manager.session
        scene = context.window_manager
        row = layout.row()
        # USER SETTINGS
        row.prop(settings, "username", text="id")
        
        row = layout.row()
        row.prop(settings, "client_color", text="color") 
        row = layout.row()


class SESSION_PT_user(bpy.types.Panel):
    bl_idname = "MULTIUSER_USER_PT_panel"
    bl_label = "Users"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'
    @classmethod
    def poll(cls, context):
        return  operators.client and operators.client.state == 2
 

    def draw(self, context):
        layout = self.layout

        settings = context.window_manager.session
        scene = context.window_manager
        # Create a simple row.
        col = layout.column(align=True)
        
        client_keys = operators.client.list(filter='BlUser')
        if client_keys and len(client_keys) > 0:
            for key in client_keys:
                area_msg = col.row(align = True)
                item_box = area_msg.box()
                client = operators.client.get(key).buffer
                info = ""
                
                detail_item_row = item_box.row(align = True)

                username = client['name']


                is_local_user =  username == settings.username
                
                if is_local_user: 
                    info = "(self)"
                
                detail_item_row.label(
                    text="{} {}".format(username, info))

                if not is_local_user:
                    detail_item_row.operator(
                        "session.snapview", text="", icon='VIEW_CAMERA').target_client = key
                row = layout.row()
        else:
            row.label(text="Empty")

        row = layout.row()


class SESSION_PT_outliner(bpy.types.Panel):
    bl_idname = "MULTIUSER_PROPERTIES_PT_panel"
    bl_label = "Properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"

    @classmethod
    def poll(cls, context):
        return  operators.client and operators.client.state == 2

    def draw_header(self, context):
        self.layout.label(text="", icon='OUTLINER_OB_GROUP_INSTANCE')
    
    def draw(self, context):
        layout = self.layout
        
        if hasattr(context.window_manager,'session'):
            settings = context.window_manager.session
            scene = context.window_manager

            row = layout.row()
            row.prop(settings,'outliner_filter', text="")

            row = layout.row(align=True)
            # Property area
            # area_msg = row.box()
            client_keys = operators.client.list()

            if client_keys and len(client_keys) > 0:
                col = layout.column(align=True)
                for key in client_keys:
                    item = operators.client.get(key)

                    if item.str_type == 'BlUser':
                        continue

                    area_msg = col.row(align = True)
                    item_box = area_msg.box()
                    name = "None"
                    #TODO: refactor that...
                    if hasattr(item.pointer,'name'):
                        name = item.pointer.name
                    else:
                        name = item.buffer['name']

                    detail_item_box = item_box.row()
                    detail_item_box.label(text="",icon=item.icon)
                    detail_item_box.label(text="{} ".format(name))
                    detail_item_box.label(text="{} ".format(item.owner))

                    if item.state == FETCHED:
                        detail_item_box.operator("session.apply", text=PROP_STATES[item.state]).target = item.uuid
                    else:
                        detail_item_box.label(text="{} ".format(PROP_STATES[item.state]))
                        
                    
                    # right_icon = "DECORATE_UNLOCKED"
                    # if owner == settings.username:
                    #     right_icon="DECORATE_UNLOCKED"
                    # else:
                        
                    #     right_icon="DECORATE_LOCKED"
                    
                    # ro = detail_item_box.operator("session.right", text="",emboss=settings.is_admin, icon=right_icon)
                    # ro.key = item[0]
                    # detail_item_box.operator(
                    #     "session.remove_prop", text="", icon="X").property_path = key
            else:
                area_msg.label(text="Empty")


classes = (
    SESSION_PT_settings,
    SESSION_PT_settings_user,
    SESSION_PT_settings_network,
    SESSION_PT_user,
    SESSION_PT_outliner,

)


register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()
