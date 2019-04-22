import bpy

from . import client, operators


class SessionSettingsPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NET settings"
    bl_idname = "SCENE_PT_SessionSettings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        if hasattr(context.scene, 'session_settings'):
            net_settings = context.scene.session_settings
            scene = context.scene

            row = layout.row()
            if operators.client_instance is None:
                
                row = layout.row()
                box = row.box()
                row = box.row()
                row.label(text="User infos")
                row = box.row()
                row.prop(scene.session_settings, "username", text="id")
                
                row = box.row()
                row.prop(scene.session_settings, "client_color", text="color") 

                row = layout.row()
                row.prop(scene.session_settings, "session_mode", expand=True)
                row = layout.row()

                if scene.session_settings.session_mode == 'HOST':
                    box = row.box()
                    row = box.row()
                    row.label(text="init scene:")
                    row.prop(net_settings, "init_scene", text="")
                    row = layout.row()
                    row.operator("session.create", text="HOST")
                else:
                    box = row.box()
                    row = box.row()
                    row.prop(net_settings, "ip", text="ip")
                    row = box.row()
                    row.label(text="port:")
                    row.prop(scene.session_settings, "port", text="")
                    row = box.row()
                    row.label(text="load data:")
                    row.prop(net_settings, "load_data", text="")
                    row = box.row()
                    row.label(text="clear scene:")
                    row.prop(net_settings, "clear_scene", text="")

                    row = layout.row()
                    row.operator("session.join", text="CONNECT")

            else:

                if operators.client_instance.agent.is_alive():
                    row = layout.row()
                    row.operator("session.stop", icon='QUIT', text="Exit")
                # elif operators.client.status is client.RCFStatus.CONNECTING:
                #     row.label(text="connecting...")
                #     row = layout.row()
                #     row.operator("session.stop", icon='QUIT', text="CANCEL")

            row = layout.row()


class SessionUsersPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NET users"
    bl_idname = "SCENE_PT_SessionUsers"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        if operators.client_instance:
            return operators.client_instance.agent.is_alive()
        return False

    def draw(self, context):
        layout = self.layout

        net_settings = context.scene.session_settings
        scene = context.scene
        # Create a simple row.
        row = layout.row()
        if operators.client_keys and len(operators.client_keys) > 0:
            for key in operators.client_keys:
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


class SessionPropertiesPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NET properties"
    bl_idname = "SCENE_PT_SessionProps"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        if operators.client_instance:
            return operators.client_instance.agent.is_alive()

        return False

    def draw(self, context):
        layout = self.layout

        if hasattr(context.scene,'session_settings'):
            net_settings = context.scene.session_settings
            scene = context.scene
            # Create a simple row.
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
            area_msg.operator("session.refresh", text="",
                        icon="UV_SYNC_SELECT")
            if operators.client_keys and len(operators.client_keys) > 0:
                for item in operators.client_keys:
                    owner =  item[1].decode()
                    item_box = area_msg.box()
                    
                    detail_item_box = item_box.row(align = True)

                    # detail_item_box = item_box.row()
                    
                    detail_item_box.label(text="{} ".format(item[0]))

                    detail_item_box.label(text="{} ".format(owner))

                    if owner == net_settings.username:
                        detail_item_box.label(text="",icon="DECORATE_UNLOCKED")
                    else:
                        
                        detail_item_box.label(text="",icon="DECORATE_LOCKED")
                    # detail_item_box.operator(
                    #     "session.remove_prop", text="", icon="X").property_path = key
            else:
                area_msg.label(text="Empty")


class SessionTaskPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NET tasks"
    bl_idname = "SCENE_PT_SessionTasks"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        if operators.client:
            return operators.client.agent.is_alive()
            # return operators.client.status == client.RCFStatus.CONNECTED
        return False

    def draw(self, context):
        layout = self.layout
        # Create a simple row.
        row = layout.row()

        if operators.update_list:
            # Property area
            area_msg = row.box()
            if len(operators.update_list) > 0:
                for key, values in operators.update_list.items():
                    item_box = area_msg.box()
                    detail_item_box = item_box.row()
                    # detail_item_box = item_box.row()
                    
                    detail_item_box.label(text="{} - {} ".format(
                        key, values))
            else:
                area_msg.label(text="Empty")


classes = (
    SessionSettingsPanel,
    SessionUsersPanel,
    SessionPropertiesPanel,
    # SessionTaskPanel,
)


register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()
