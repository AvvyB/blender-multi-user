# ##### BEGIN GPL LICENSE BLOCK #####
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


import bpy

from .utils import get_preferences, get_expanded_icon, get_folder_size, get_state_str
from replication.constants import (ADDED, ERROR, FETCHED,
                                                     MODIFIED, RP_COMMON, UP,
                                                     STATE_ACTIVE, STATE_AUTH,
                                                     STATE_CONFIG, STATE_SYNCING,
                                                     STATE_INITIAL, STATE_SRV_SYNC,
                                                     STATE_WAITING, STATE_QUITTING,
                                                     STATE_LOBBY,
                                                     STATE_LAUNCHING_SERVICES)
from replication import __version__
from replication.interface import session

ICONS_PROP_STATES = ['TRIA_DOWN',  # ADDED
                     'TRIA_UP',  # COMMITED
                     'KEYTYPE_KEYFRAME_VEC',  # PUSHED
                     'TRIA_DOWN',  # FETCHED
                     'RECOVER_LAST',   # RESET
                     'TRIA_UP', # CHANGED
                     'ERROR']  # ERROR


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', fill_empty='  '):
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
    From here:    
    https://gist.github.com/greenstick/b23e475d2bfdc3a82e34eaa1f6781ee4
    """
    if total == 0:
        return ""
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + fill_empty * (length - filledLength)
    return f"{prefix} |{bar}| {iteration}/{total}{suffix}"


class SESSION_PT_settings(bpy.types.Panel):
    """Settings panel"""
    bl_idname = "MULTIUSER_SETTINGS_PT_panel"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Multiuser"

    def draw_header(self, context):
        layout = self.layout
        if session and session.state['STATE'] != STATE_INITIAL:
            cli_state = session.state
            state =  session.state.get('STATE')
            connection_icon = "KEYTYPE_MOVING_HOLD_VEC"

            if state == STATE_ACTIVE:
                connection_icon = 'PROP_ON'
            else:
                connection_icon = 'PROP_CON'

            layout.label(text=f"Session - {get_state_str(cli_state['STATE'])}", icon=connection_icon)
        else:
            layout.label(text=f"Session - v{__version__}",icon="PROP_OFF")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        runtime_settings = context.window_manager.session
        settings = get_preferences()

        if hasattr(context.window_manager, 'session'):
            # STATE INITIAL
            if not session \
               or (session and session.state['STATE'] == STATE_INITIAL):
                pass
            else:
                cli_state = session.state                
                row = layout.row()

                current_state = cli_state['STATE']
                info_msg = None

                if current_state in [STATE_ACTIVE]:
                    row = row.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
                    row.prop(settings.sync_flags, "sync_render_settings",text="",icon_only=True, icon='SCENE')
                    row.prop(settings.sync_flags, "sync_during_editmode", text="",icon_only=True, icon='EDITMODE_HLT')
                    row.prop(settings.sync_flags, "sync_active_camera", text="",icon_only=True, icon='OBJECT_DATAMODE')

                row= layout.row()

                if current_state in [STATE_ACTIVE] and runtime_settings.is_host:
                    info_msg = f"LAN: {runtime_settings.internet_ip}" 
                if current_state == STATE_LOBBY:
                    info_msg = "Waiting for the session to start."

                if info_msg:
                    info_box = row.box()
                    info_box.row().label(text=info_msg,icon='INFO')

                # Progress bar
                if current_state in [STATE_SYNCING, STATE_SRV_SYNC, STATE_WAITING]:
                    info_box = row.box()
                    info_box.row().label(text=printProgressBar(
                        cli_state['CURRENT'],
                        cli_state['TOTAL'],
                        length=16
                    ))

                layout.row().operator("session.stop", icon='QUIT', text="Exit")

class SESSION_PT_settings_network(bpy.types.Panel):
    bl_idname = "MULTIUSER_SETTINGS_NETWORK_PT_panel"
    bl_label = "Network"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'

    @classmethod
    def poll(cls, context):
        return not session \
            or (session and session.state['STATE'] == 0)

    def draw_header(self, context):
        self.layout.label(text="", icon='URL')

    def draw(self, context):
        layout = self.layout

        runtime_settings = context.window_manager.session
        settings = get_preferences()

        # USER SETTINGS
        row = layout.row()
        row.prop(runtime_settings, "session_mode", expand=True)
        row = layout.row()

        box = row.box()

        if runtime_settings.session_mode == 'HOST':
            row = box.row()
            row.label(text="Port:")
            row.prop(settings, "port", text="")
            row = box.row()
            row.label(text="Start from:")
            row.prop(settings, "init_method", text="")
            row = box.row()
            row.label(text="Admin password:")
            row.prop(runtime_settings, "password", text="")
            row = box.row()
            row.operator("session.start", text="HOST").host = True
        else:
            row = box.row()
            row.prop(settings, "ip", text="IP")
            row = box.row()
            row.label(text="Port:")
            row.prop(settings, "port", text="")

            row = box.row()
            row.prop(runtime_settings, "admin", text='Connect as admin', icon='DISCLOSURE_TRI_DOWN' if runtime_settings.admin
                     else 'DISCLOSURE_TRI_RIGHT')
            if runtime_settings.admin:
                row = box.row()
                row.label(text="Password:")
                row.prop(runtime_settings, "password", text="")
            row = box.row()
            row.operator("session.start", text="CONNECT").host = False


class SESSION_PT_settings_user(bpy.types.Panel):
    bl_idname = "MULTIUSER_SETTINGS_USER_PT_panel"
    bl_label = "User info"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'

    @classmethod
    def poll(cls, context):
        return not session \
            or (session and session.state['STATE'] == 0)
    
    def draw_header(self, context):
        self.layout.label(text="", icon='USER')

    def draw(self, context):
        layout = self.layout

        runtime_settings = context.window_manager.session
        settings = get_preferences()

        row = layout.row()
        # USER SETTINGS
        row.prop(settings, "username", text="name")

        row = layout.row()
        row.prop(settings, "client_color", text="color")
        row = layout.row()


class SESSION_PT_advanced_settings(bpy.types.Panel):
    bl_idname = "MULTIUSER_SETTINGS_REPLICATION_PT_panel"
    bl_label = "Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return not session \
            or (session and session.state['STATE'] == 0)

    def draw_header(self, context):
        self.layout.label(text="", icon='PREFERENCES')
        
    def draw(self, context):
        layout = self.layout

        runtime_settings = context.window_manager.session
        settings = get_preferences()

        
        net_section = layout.row().box()
        net_section.prop(
            settings,
            "sidebar_advanced_net_expanded",
            text="Network",
            icon=get_expanded_icon(settings.sidebar_advanced_net_expanded), 
            emboss=False)
        
        if settings.sidebar_advanced_net_expanded:
            net_section_row = net_section.row()
            net_section_row.label(text="IPC Port:")
            net_section_row.prop(settings, "ipc_port", text="")
            net_section_row = net_section.row()
            net_section_row.label(text="Timeout (ms):")
            net_section_row.prop(settings, "connection_timeout", text="")

        replication_section = layout.row().box()
        replication_section.prop(
            settings,
            "sidebar_advanced_rep_expanded",
            text="Replication",
            icon=get_expanded_icon(settings.sidebar_advanced_rep_expanded), 
            emboss=False)

        if settings.sidebar_advanced_rep_expanded:
            replication_section_row = replication_section.row()

            replication_section_row.label(text="Sync flags", icon='COLLECTION_NEW')
            replication_section_row = replication_section.row()
            replication_section_row.prop(settings.sync_flags, "sync_render_settings")
            replication_section_row = replication_section.row()
            replication_section_row.prop(settings.sync_flags, "sync_active_camera")
            replication_section_row = replication_section.row()

            replication_section_row.prop(settings.sync_flags, "sync_during_editmode")
            replication_section_row = replication_section.row()
            if settings.sync_flags.sync_during_editmode:
                warning = replication_section_row.box()
                warning.label(text="Don't use this with heavy meshes !", icon='ERROR')
                replication_section_row = replication_section.row()

            replication_section_row.label(text="Update method", icon='RECOVER_LAST')
            replication_section_row = replication_section.row()
            replication_section_row.prop(settings, "update_method", expand=True)
            replication_section_row = replication_section.row()
            replication_timers = replication_section_row.box()
            replication_timers.label(text="Replication timers", icon='TIME')
            if settings.update_method == "DEFAULT":
                replication_timers = replication_timers.row()
                # Replication frequencies
                flow = replication_timers.grid_flow(
                    row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
                line = flow.row(align=True)
                line.label(text=" ")
                line.separator()
                line.label(text="refresh (sec)")
                line.label(text="apply (sec)")

                for item in settings.supported_datablocks:
                    line = flow.row(align=True)
                    line.prop(item, "auto_push", text="", icon=item.icon)
                    line.separator()
                    line.prop(item, "bl_delay_refresh", text="")
                    line.prop(item, "bl_delay_apply", text="")
            else:
                replication_timers = replication_timers.row()
                replication_timers.label(text="Update rate (ms):")
                replication_timers.prop(settings, "depsgraph_update_rate", text="")
        
        cache_section = layout.row().box()
        cache_section.prop(
            settings,
            "sidebar_advanced_cache_expanded",
            text="Cache",
            icon=get_expanded_icon(settings.sidebar_advanced_cache_expanded), 
            emboss=False)
        if settings.sidebar_advanced_cache_expanded:
            cache_section_row = cache_section.row()
            cache_section_row.label(text="Cache directory:")
            cache_section_row = cache_section.row()
            cache_section_row.prop(settings, "cache_directory", text="")
            cache_section_row = cache_section.row()
            cache_section_row.label(text="Clear memory filecache:")
            cache_section_row.prop(settings, "clear_memory_filecache", text="")
            cache_section_row = cache_section.row()
            cache_section_row.operator('session.clear_cache', text=f"Clear cache ({get_folder_size(settings.cache_directory)})")
        log_section = layout.row().box()
        log_section.prop(
            settings,
            "sidebar_advanced_log_expanded",
            text="Logging",
            icon=get_expanded_icon(settings.sidebar_advanced_log_expanded), 
            emboss=False)

        if settings.sidebar_advanced_log_expanded:
            log_section_row = log_section.row()
            log_section_row.label(text="Log level:")
            log_section_row.prop(settings, 'logging_level', text="")
class SESSION_PT_user(bpy.types.Panel):
    bl_idname = "MULTIUSER_USER_PT_panel"
    bl_label = "Online users"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'

    @classmethod
    def poll(cls, context):
        return session and session.state['STATE'] in [STATE_ACTIVE, STATE_LOBBY]

    def draw_header(self, context):
        self.layout.label(text="", icon='USER')

    def draw(self, context):
        layout = self.layout
        online_users = context.window_manager.online_users
        selected_user = context.window_manager.user_index
        settings = get_preferences()
        active_user = online_users[selected_user] if len(
            online_users)-1 >= selected_user else 0
        runtime_settings = context.window_manager.session

        # Create a simple row.
        row = layout.row()
        box = row.box()
        split = box.split(factor=0.35)
        split.label(text="user")
        split = split.split(factor=0.5)
        split.label(text="location")
        split.label(text="frame")
        split.label(text="ping")

        row = layout.row()
        layout.template_list("SESSION_UL_users",  "",  context.window_manager,
                             "online_users", context.window_manager,  "user_index")

        if active_user != 0 and active_user.username != settings.username:
            row = layout.row()
            user_operations = row.split()
            if  session.state['STATE'] == STATE_ACTIVE:
                
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

            if session.online_users[settings.username]['admin']:
                user_operations.operator(
                    "session.kick",
                    text="",
                    icon='CANCEL').user = active_user.username


class SESSION_UL_users(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        settings = get_preferences()
        is_local_user = item.username == settings.username
        ping = '-'
        frame_current = '-'
        scene_current = '-'
        status_icon = 'BLANK1'
        if session:
            user = session.online_users.get(item.username)
            if user:
                ping = str(user['latency'])
                metadata = user.get('metadata')
                if metadata and 'frame_current' in metadata:
                    frame_current = str(metadata.get('frame_current','-'))
                    scene_current = metadata.get('scene_current','-')
                if user['admin']:
                    status_icon = 'FAKE_USER_ON'
        split = layout.split(factor=0.35)
        split.label(text=item.username, icon=status_icon)
        split = split.split(factor=0.5)
        split.label(text=scene_current)
        split.label(text=frame_current)
        split.label(text=ping)


class SESSION_PT_presence(bpy.types.Panel):
    bl_idname = "MULTIUSER_MODULE_PT_panel"
    bl_label = "Presence overlay"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return not session \
            or (session and session.state['STATE'] in [STATE_INITIAL, STATE_ACTIVE])

    def draw_header(self, context):
        self.layout.prop(context.window_manager.session,
                         "enable_presence", text="",icon='OVERLAY')

    def draw(self, context):
        layout = self.layout

        settings = context.window_manager.session
        pref = get_preferences()
        layout.active = settings.enable_presence
        col = layout.column()
        col.prop(settings, "presence_show_session_status")
        row = col.column()
        row.active = settings.presence_show_session_status
        row.prop(pref, "presence_hud_scale", expand=True)
        row = col.column(align=True)
        row.active = settings.presence_show_session_status
        row.prop(pref, "presence_hud_hpos", expand=True)
        row.prop(pref, "presence_hud_vpos", expand=True)
        col.prop(settings, "presence_show_selected")
        col.prop(settings, "presence_show_user")
        row = layout.column()
        row.active = settings.presence_show_user
        row.prop(settings, "presence_show_far_user")

def draw_property(context, parent, property_uuid, level=0):
    settings = get_preferences()
    runtime_settings = context.window_manager.session
    item = session.get(uuid=property_uuid)

    area_msg = parent.row(align=True)

    if item.state == ERROR:
        area_msg.alert=True
    else:
        area_msg.alert=False

    line = area_msg.box()

    name = item.data['name'] if item.data else item.uuid

    detail_item_box = line.row(align=True)

    detail_item_box.label(text="",
                          icon=settings.supported_datablocks[item.str_type].icon)
    detail_item_box.label(text=f"{name}")

    # Operations

    have_right_to_modify = (item.owner == settings.username or \
        item.owner == RP_COMMON) and item.state != ERROR

    if have_right_to_modify:
        detail_item_box.operator(
            "session.commit",
            text="",
            icon='TRIA_UP').target = item.uuid
        detail_item_box.separator()

    if item.state in [FETCHED, UP]:
        apply = detail_item_box.operator(
            "session.apply",
            text="",
            icon=ICONS_PROP_STATES[item.state])
        apply.target = item.uuid
        apply.reset_dependencies = True
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

class SESSION_PT_repository(bpy.types.Panel):
    bl_idname = "MULTIUSER_PROPERTIES_PT_panel"
    bl_label = "Repository"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_panel'

    @classmethod
    def poll(cls, context):
        settings = get_preferences()
        admin = False

        if session and hasattr(session,'online_users'):
            usr = session.online_users.get(settings.username)
            if usr:
                admin = usr['admin']
        return hasattr(context.window_manager, 'session') and \
            session and \
            (session.state['STATE'] == STATE_ACTIVE or \
            session.state['STATE'] == STATE_LOBBY and admin)

    def draw_header(self, context):
        self.layout.label(text="", icon='OUTLINER_OB_GROUP_INSTANCE')
        self.layout.operator('session.export',text="", icon="EXPORT")

    def draw(self, context):
        layout = self.layout

        # Filters
        settings = get_preferences()
        runtime_settings = context.window_manager.session

        usr = session.online_users.get(settings.username)

        row = layout.row()

        if session.state['STATE'] == STATE_ACTIVE:
            flow = layout.grid_flow(
                row_major=True,
                columns=0,
                even_columns=True,
                even_rows=False,
                align=True)

            for item in settings.supported_datablocks:
                col = flow.column(align=True)
                col.prop(item, "use_as_filter", text="", icon=item.icon)

            row = layout.row(align=True)
            row.prop(runtime_settings, "filter_owned", text="Show only owned")

            row = layout.row(align=True)

            # Properties
            types_filter = [t.type_name for t in settings.supported_datablocks
                            if t.use_as_filter]

            key_to_filter = session.list(
                filter_owner=settings.username) if runtime_settings.filter_owned else session.list()

            client_keys = [key for key in key_to_filter
                           if session.get(uuid=key).str_type
                           in types_filter]

            if client_keys:
                col = layout.column(align=True)
                for key in client_keys:
                    draw_property(context, col, key)

            else:
                row.label(text="Empty")

        elif session.state['STATE'] == STATE_LOBBY and usr and usr['admin']:
            row.operator("session.init", icon='TOOL_SETTINGS', text="Init")
        else:
            row.label(text="Waiting to start")

class VIEW3D_PT_overlay_session(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_parent_id = 'VIEW3D_PT_overlay'
    bl_label = "Multi-user"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout

        view = context.space_data
        overlay = view.overlay
        display_all = overlay.show_overlays

        col = layout.column()

        row = col.row(align=True)
        settings = context.window_manager.session
        layout.active = settings.enable_presence
        col = layout.column()
        col.prop(settings, "presence_show_session_status")
        col.prop(settings, "presence_show_selected")
        col.prop(settings, "presence_show_user")

        row = layout.column()
        row.active = settings.presence_show_user
        row.prop(settings, "presence_show_far_user")

classes = (
    SESSION_UL_users,
    SESSION_PT_settings,
    SESSION_PT_settings_user,
    SESSION_PT_settings_network,
    SESSION_PT_presence,
    SESSION_PT_advanced_settings,
    SESSION_PT_user,
    SESSION_PT_repository,
    VIEW3D_PT_overlay_session,
)


register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()
