import bpy

from . import net_components, net_operators


class SessionSettingsPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NET settings"
    bl_idname = "SCENE_PT_SessionSettings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        net_settings = context.scene.session_settings
        scene = context.scene

        row = layout.row()
        if net_operators.client is None:
            row = layout.row()
            row.prop(scene.session_settings, "username", text="username:")

            row = layout.row()
            row.prop(scene.session_settings, "session_mode", expand=True)
            row = layout.row()

            if scene.session_settings.session_mode == 'HOST':
                row.operator("session.create", text="HOST")
            else:
                box = row.box()
                row = box.row()
                row.prop(net_settings, "ip", text="server ip")
                row = box.row()
                row.label(text="load data:")
                row.prop(net_settings, "load_data", text="")
                row = box.row()
                row.label(text="clear scene:")
                row.prop(net_settings, "clear_scene", text="")

                row = layout.row()
                row.operator("session.join", text="CONNECT")

        else:

            if net_operators.client.status is net_components.RCFStatus.CONNECTED:
                row.label(text="Net frequency:")
                row.prop(net_settings, "update_frequency", text="")
                row = layout.row()
                row.operator("session.stop", icon='QUIT', text="Exit")
            elif net_operators.client.status is net_components.RCFStatus.CONNECTING:
                row.label(text="connecting...")
                row = layout.row()
                row.operator("session.stop", icon='QUIT', text="CANCEL")

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
        if net_operators.client:
            return net_operators.client.status == net_components.RCFStatus.CONNECTED
        return False

    def draw(self, context):
        layout = self.layout

        net_settings = context.scene.session_settings
        scene = context.scene
        # Create a simple row.
        row = layout.row()
        if net_operators.client:
            if len(net_operators.client.property_map) > 0:
                for key, values in net_operators.client.property_map.items():
                    if 'client' in key:
                        info = ""
                        item_box = row.box()
                        detail_item_box = item_box.row()

                        if values.id == net_operators.client.id:
                            info = "(self)"
                        # detail_item_box = item_box.row()
                        detail_item_box.label(
                            text="{} {}".format(values.id.decode(), info))

                        if net_operators.client.id.decode() not in key:
                            detail_item_box.operator(
                                "session.snapview", text="", icon='VIEW_CAMERA').target_client = values.id.decode()
                        row = layout.row()
            else:
                row.label(text="Empty")

            row = layout.row()


class SessionPropertiesPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "NET properties"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    @classmethod
    def poll(cls, context):
        if net_operators.client:
            return net_operators.client.status == net_components.RCFStatus.CONNECTED
        return False

    def draw(self, context):
        layout = self.layout

        net_settings = context.scene.session_settings
        scene = context.scene
        # Create a simple row.
        row = layout.row()

        if net_operators.client:
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
            if len(net_operators.client.property_map) > 0:
                for key, values in net_operators.client.property_map.items():
                    item_box = area_msg.box()
                    detail_item_box = item_box.row()
                    # detail_item_box = item_box.row()
                    detail_item_box.label(text="{} ({}) {} ".format(
                        key, values.mtype, values.id.decode()))
                    detail_item_box.operator(
                        "session.remove_prop", text="", icon="X").property_path = key
            else:
                area_msg.label(text="Empty")


classes = (
    SessionSettingsPanel,
    SessionUsersPanel,
    SessionPropertiesPanel,
)


register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()
