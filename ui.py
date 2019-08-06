import bpy
from . import operators


ICONS = {'Image': 'IMAGE_DATA', 'Curve':'CURVE_DATA', 'Client':'SOLO_ON','Collection': 'FILE_FOLDER', 'Mesh': 'MESH_DATA', 'Object': 'OBJECT_DATA', 'Material': 'MATERIAL_DATA',
                  'Texture': 'TEXTURE_DATA', 'Scene': 'SCENE_DATA','AreaLight':'LIGHT_DATA', 'Light': 'LIGHT_DATA', 'SpotLight': 'LIGHT_DATA', 'SunLight': 'LIGHT_DATA', 'PointLight': 'LIGHT_DATA', 'Camera': 'CAMERA_DATA', 'Action': 'ACTION', 'Armature': 'ARMATURE_DATA', 'GreasePencil': 'GREASEPENCIL'}

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

        if hasattr(context.window_manager, 'session'):
            net_settings = context.window_manager.session
            window_manager = context.window_manager

            row = layout.row()
            # STATE INITIAL
            if not operators.client or (operators.client and operators.client.state == 0):
                row = layout.row()

                # USER SETTINGS
                box = row.box()
                row = box.row()
                row.label(text="USER", icon='TRIA_RIGHT')
                row = box.row()
                row.prop(window_manager.session, "username", text="id")
                
                row = box.row()
                row.prop(window_manager.session, "client_color", text="color") 
                row = box.row()

                


                # NETWORK SETTINGS
                row = layout.row()
                box = row.box()
                row = box.row()
                row.label(text="NETWORK", icon = "TRIA_RIGHT")
                
                row = box.row()
                row.label(text="draw overlay:")
                row.prop(net_settings, "enable_presence", text="")
                row = box.row()
                row.label(text="clear blend:")
                row.prop(net_settings, "start_empty", text="")
                row = box.row()
            
                row = box.row()
                row.prop(net_settings, "session_mode", expand=True)
                row = box.row()

                if window_manager.session.session_mode == 'HOST':
                    box = row.box()
                    row = box.row()
                    row.label(text="init scene:")
                    row.prop(net_settings, "init_scene", text="")
                    row = box.row()
                    row.operator("session.start", text="HOST").host = True
                else:
                    box = row.box()
                    row = box.row()
                    row.prop(net_settings, "ip", text="ip")
                    row = box.row()
                    row.label(text="port:")
                    row.prop(window_manager.session, "port", text="")
                    row = box.row()
                    row.label(text="load data:")
                    row.prop(net_settings, "load_data", text="")
                    

                    row = box.row()
                    row.operator("session.start", text="CONNECT").host = False

                # REPLICATION SETTINGS
                row = layout.row()
                box = row.box()
                row = box.row()
                row.label(text="REPLICATION", icon='TRIA_RIGHT')
                row = box.row()    
                
                for item in window_manager.session.supported_datablock:
                    row.label(text=item.type_name,icon=ICONS[item.type_name])
                    row.prop(item, "is_replicated", text="") 
                    row = box.row()


                

            else:
                 # STATE ACTIVE
                if operators.client.state ==  2:
                    
                    row = layout.row()
                    row.operator("session.stop", icon='QUIT', text="Exit")
                    # row = layout.row(align=True)
                    # row.operator("session.dump", icon='QUIT', text="Dump")
                    # row.operator("session.dump", icon='QUIT', text="Load")
                    row = layout.row()

                # STATE SYNCING
                else:    
                    status = "connecting..."
                    if net_settings.is_admin:
                        status =  "init scene...({} tasks remaining)".format(operators.client.active_tasks)
                    row.label(text=status)
                    row = layout.row()
                    row.operator("session.stop", icon='QUIT', text="CANCEL")


            row = layout.row()


class SESSION_PT_user(bpy.types.Panel):
    bl_idname = "MULTIUSER_USER_PT_panel"
    bl_label = "Users online"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"
    @classmethod
    def poll(cls, context):
        return  operators.client and operators.client.state == 2
 

    def draw(self, context):
        layout = self.layout

        net_settings = context.window_manager.session
        scene = context.window_manager
        # Create a simple row.
        row = layout.row()
        client_keys = operators.client.list()
        if client_keys and len(client_keys) > 0:
            for key in client_keys:
                if 'Client' in key[0]:
                    info = ""
                    item_box = row.box()
                    detail_item_box = item_box.row()

                    username = key[0].split('/')[1]
                    if username == net_settings.username:
                        info = "(self)"
                    # detail_item_box = item_box.row()
                    detail_item_box.label(
                        text="{} - {}".format(username, info))

                    if net_settings.username not in key[0]:
                        detail_item_box.operator(
                            "session.snapview", text="", icon='VIEW_CAMERA').target_client = username
                    row = layout.row()
        else:
            row.label(text="Empty")

        row = layout.row()


def get_client_key(item):
    return item[0]

class SESSION_PT_properties(bpy.types.Panel):
    bl_idname = "MULTIUSER_PROPERTIES_PT_panel"
    bl_label = "Replicated properties"
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
            net_settings = context.window_manager.session
            scene = context.window_manager

            row = layout.row()

            row = layout.row(align=True)
            row.prop(net_settings, "buffer", text="")
            row.prop(net_settings, "add_property_depth", text="")
            add = row.operator("session.add_prop", text="",
                        icon="ADD")
            add.property_path = net_settings.buffer
            add.depth = net_settings.add_property_depth
            row = layout.row()

            # Property area
            area_msg = row.box()
            client_keys = operators.client.list()
            if client_keys and len(client_keys) > 0:

                for item in sorted(client_keys, key=get_client_key):
                    owner = 'toto'
                    try:
                        owner =  item[1]
                    except:
                        owner =  item[1].decode()
                        pass
                    
                    store_type,store_name =  item[0].split('/')
                    item_box = area_msg.box()
                    
                    detail_item_box = item_box.row(align = True)
                    detail_item_box.label(text="",icon=ICONS[store_type])
                    detail_item_box.label(text="{} ".format(store_name))
                    detail_item_box.label(text="{} ".format(owner))

                    right_icon = "DECORATE_UNLOCKED"
                    if owner == net_settings.username:
                        right_icon="DECORATE_UNLOCKED"
                    else:
                        
                        right_icon="DECORATE_LOCKED"
                    
                    ro = detail_item_box.operator("session.right", text="",emboss=net_settings.is_admin, icon=right_icon)
                    ro.key = item[0]
                    # detail_item_box.operator(
                    #     "session.remove_prop", text="", icon="X").property_path = key
            else:
                area_msg.label(text="Empty")


classes = (
    SESSION_PT_settings,
    SESSION_PT_user,
    SESSION_PT_properties,

)


register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()
