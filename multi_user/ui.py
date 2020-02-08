import bpy

from . import operators
from .libs.replication.replication.constants import (ADDED, ERROR, FETCHED,
                                                     MODIFIED, RP_COMMON, UP,
                                                     STATE_ACTIVE, STATE_AUTH,
                                                     STATE_CONFIG, STATE_SYNCING,
                                                     STATE_INITIAL, STATE_SRV_SYNC,
                                                     STATE_WAITING)

ICONS_PROP_STATES = ['TRIA_DOWN',  # ADDED
                     'TRIA_UP',  # COMMITED
                     'KEYTYPE_KEYFRAME_VEC',  # PUSHED
                     'TRIA_DOWN',  # FETCHED
                     'FILE_REFRESH',   # UP
                     'TRIA_UP']  # CHANGED

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', fill_empty='  '):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + fill_empty * (length - filledLength)
    return '{} |{}| {}%{}'.format(prefix, bar, percent, suffix)

def get_state_str(state):
    state_str = 'None'
    if state == STATE_WAITING:
        state_str = 'WARMING UP DATA'
    elif state == STATE_SYNCING:
        state_str = 'FETCHING FROM SERVER'
    elif state == STATE_AUTH:
        state_str = 'AUTHENTIFICATION'
    elif state == STATE_CONFIG:
        state_str = 'CONFIGURATION'
    elif state == STATE_ACTIVE:
        state_str = 'ONLINE'
    elif state == STATE_SRV_SYNC:
        state_str = 'PUSHING TO SERVER'
    return state_str

class SESSION_PT_settings(bpy.types.Panel):
    """Settings panel"""
    bl_idname = "MULTIUSER_SETTINGS_PT_panel"
    bl_label = "Session"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"

    def draw_header(self, context):
        self.layout.label(text="", icon='TOOL_SETTINGS')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        row = layout.row()

        if hasattr(context.window_manager, 'session'):
            # STATE INITIAL
            if not operators.client \
               or (operators.client and operators.client.state['STATE'] == STATE_INITIAL):
                pass
            else:
                cli_state = operators.client.state
                
                row.label(text=f"Status : {get_state_str(cli_state['STATE'])}")
                row = layout.row()
                
                # STATE ACTIVE
                if cli_state['STATE'] == STATE_ACTIVE:
                    row.operator("session.stop", icon='QUIT', text="Exit")
                    row = layout.row()

                # STATE SYNCING
                else:
                    box = row.box()
                    if cli_state['STATE'] in [STATE_SYNCING,STATE_SRV_SYNC,STATE_WAITING]:
                        box.label(text=printProgressBar(
                            cli_state['CURRENT'],
                            cli_state['TOTAL'],
                            length=16
                        ))

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
        return not operators.client \
            or (operators.client and operators.client.state['STATE'] == 0)

    def draw(self, context):
        layout = self.layout

        settings = context.window_manager.session

        # USER SETTINGS
        row = layout.row()
        row.prop(settings, "session_mode", expand=True)
        row = layout.row()

        if settings.session_mode == 'HOST':
            box = row.box()
            row = box.row()
            row.label(text="Start empty:")
            row.prop(settings, "start_empty", text="")
            row = box.row()
            row.label(text="Port:")
            row.prop(settings, "port", text="")
            row = box.row()
            row.label(text="IPC Port:")
            row.prop(settings, "ttl_port", text="")
            row = box.row()
            row.operator("session.start", text="HOST").host = True
        else:
            box = row.box()
            row = box.row()
            row.prop(settings, "ip", text="IP")
            row = box.row()
            row.label(text="Port:")
            row.prop(settings, "port", text="")
            row = box.row()
            row.label(text="IPC Port:")
            row.prop(settings, "ttl_port", text="")

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
        return not operators.client \
            or (operators.client and operators.client.state['STATE'] == 0)

    def draw(self, context):
        layout = self.layout

        settings = context.window_manager.session

        row = layout.row()
        # USER SETTINGS
        row.prop(settings, "username", text="name")

        row = layout.row()
        row.prop(settings, "client_color", text="color")
        row = layout.row()


class SESSION_PT_settings_replication(bpy.types.Panel):
    bl_idname = "MULTIUSER_SETTINGS_REPLICATION_PT_panel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return not operators.client \
            or (operators.client and operators.client.state['STATE'] == 0)

    def draw(self, context):
        layout = self.layout

        settings = context.window_manager.session
        # Right managment
        if settings.session_mode == 'HOST':
            row = layout.row(align=True)
            row.label(text="Right strategy:")
            row.prop(settings,"right_strategy",text="")

        row = layout.row()

        row = layout.row()
        # Replication frequencies
        flow = row .grid_flow(
            row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
        line = flow.row(align=True)
        line.label(text=" ")
        line.separator()
        line.label(text="refresh (sec)")
        line.label(text="apply (sec)")

        for item in settings.supported_datablock:
            line = flow.row(align=True)
            line.prop(item, "auto_push", text="", icon=item.icon)
            line.separator()
            line.prop(item, "bl_delay_refresh", text="")
            line.prop(item, "bl_delay_apply", text="")


class SESSION_PT_user(bpy.types.Panel):
    bl_idname = "MULTIUSER_USER_PT_panel"
    bl_label = "Online users"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'

    @classmethod
    def poll(cls, context):
        return operators.client and operators.client.state['STATE'] == 2

    def draw(self, context):
        layout = self.layout
        online_users = context.window_manager.online_users
        selected_user = context.window_manager.user_index
        settings = context.window_manager.session
        active_user =  online_users[selected_user] if len(online_users)-1>=selected_user else 0
        

        # Create a simple row.
        row = layout.row()
        box = row.box()
        split = box.split(factor=0.5)
        split.label(text="user")
        split.label(text="frame")
        split.label(text="ping")

        row = layout.row()
        layout.template_list("SESSION_UL_users", "",  context.window_manager, "online_users", context.window_manager,  "user_index")

        if active_user != 0 and active_user.username != settings.username:
            row = layout.row()
            user_operations = row.split()
            user_operations.alert = context.window_manager.session.time_snap_running
            user_operations.operator(
                "session.snapview",
                text="",
                icon='VIEW_CAMERA').target_client = active_user.username
            
            user_operations.alert = context.window_manager.session.user_snap_running
            user_operations.operator(
                "session.snaptime",
                text="",
                icon='TIME').target_client = active_user.username


class SESSION_UL_users(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        session = operators.client
        settings = context.window_manager.session
        is_local_user = item.username == settings.username
        ping = '-'
        frame_current = '-'
        if session:
            user = session.online_users.get(item.username)
            if user:
                ping = str(user['latency'])
                metadata = user.get('metadata')
                if metadata and 'frame_current' in metadata:
                    frame_current = str(metadata['frame_current'])
        
        split = layout.split(factor=0.5)
        split.label(text=item.username)
        split.label(text=frame_current)
        split.label(text=ping)
    

class SESSION_PT_presence(bpy.types.Panel):
    bl_idname = "MULTIUSER_MODULE_PT_panel"
    bl_label = "Presence overlay"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return not operators.client \
            or (operators.client and operators.client.state['STATE'] in [STATE_INITIAL, STATE_ACTIVE])

    def draw_header(self, context):
        self.layout.prop(context.window_manager.session, "enable_presence", text="")

    def draw(self, context):
        layout = self.layout

        settings = context.window_manager.session
        layout.active = settings.enable_presence
        col = layout.column()
        col.prop(settings,"presence_show_selected")
        col.prop(settings,"presence_show_user")
        row = layout.row()


def draw_property(context, parent, property_uuid, level=0):
    settings = context.window_manager.session
    item = operators.client.get(uuid=property_uuid)

    if item.state == ERROR:
        return

    area_msg = parent.row(align=True)
    if level > 0:
        for i in range(level):
            area_msg.label(text="")
    line = area_msg.box()

    name = item.data['name'] if item.data else item.uuid

    detail_item_box = line.row(align=True)

    detail_item_box.label(text="",
                          icon=settings.supported_datablock[item.str_type].icon)
    detail_item_box.label(text="{} ".format(name))

    # Operations

    have_right_to_modify = settings.is_admin or \
        item.owner == settings.username or \
        item.owner == RP_COMMON
        
    if have_right_to_modify:
        detail_item_box.operator(
            "session.commit",
            text="",
            icon='TRIA_UP').target = item.uuid
        detail_item_box.separator()
    
    if item.state in [FETCHED, UP]:
        detail_item_box.operator(
            "session.apply",
            text="",
            icon=ICONS_PROP_STATES[item.state]).target = item.uuid
    elif item.state in [MODIFIED, ADDED]:
        detail_item_box.operator(
            "session.commit",
            text="",
            icon=ICONS_PROP_STATES[item.state]).target = item.uuid
    else:
        detail_item_box.label(text="", icon=ICONS_PROP_STATES[item.state])

    right_icon = "DECORATE_UNLOCKED"
    if not have_right_to_modify:
        right_icon = "DECORATE_LOCKED"

    if have_right_to_modify:
        ro = detail_item_box.operator(
            "session.right", text="", icon=right_icon)
        ro.key = property_uuid

        detail_item_box.operator(
            "session.remove_prop", text="", icon="X").property_path = property_uuid
    else:
        detail_item_box.label(text="", icon="DECORATE_LOCKED")


class SESSION_PT_outliner(bpy.types.Panel):
    bl_idname = "MULTIUSER_PROPERTIES_PT_panel"
    bl_label = "Properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"

    @classmethod
    def poll(cls, context):
        return operators.client and operators.client.state['STATE'] == 2

    def draw_header(self, context):
        self.layout.label(text="", icon='OUTLINER_OB_GROUP_INSTANCE')

    def draw(self, context):
        layout = self.layout

        if hasattr(context.window_manager, 'session'):
            # Filters
            settings = context.window_manager.session
            flow = layout.grid_flow(
                row_major=True,
                columns=0,
                even_columns=True,
                even_rows=False,
                align=True)

            for item in settings.supported_datablock:
                col = flow.column(align=True)
                col.prop(item, "use_as_filter", text="", icon=item.icon)

            row = layout.row(align=True)
            row.prop(settings, "filter_owned", text="Show only owned")

            row = layout.row(align=True)

            # Properties
            types_filter = [t.type_name for t in settings.supported_datablock
                            if t.use_as_filter]

            key_to_filter = operators.client.list(
                filter_owner=settings.username) if settings.filter_owned else operators.client.list()

            client_keys = [key for key in key_to_filter
                           if operators.client.get(uuid=key).str_type
                           in types_filter]

            if client_keys and len(client_keys) > 0:
                col = layout.column(align=True)
                for key in client_keys:
                    draw_property(context, col, key)

            else:
                row.label(text="Empty")


classes = (
    SESSION_UL_users,
    SESSION_PT_settings,
    SESSION_PT_settings_user,
    SESSION_PT_settings_network,
    SESSION_PT_presence,
    SESSION_PT_settings_replication,
    SESSION_PT_user,
    SESSION_PT_outliner
)


register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()
