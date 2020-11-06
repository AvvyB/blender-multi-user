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

import random
import logging
import bpy
import string
import re
import os

from pathlib import Path

from . import bl_types, environment, addon_updater_ops, presence, ui
from .utils import get_preferences, get_expanded_icon
from replication.constants import RP_COMMON
from replication.interface import session

# From https://stackoverflow.com/a/106223
IP_REGEX = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
HOSTNAME_REGEX = re.compile("^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$")

def randomColor():
    """Generate a random color """
    r = random.random()
    v = random.random()
    b = random.random()
    return [r, v, b]


def random_string_digits(stringLength=6):
    """Generate a random string of letters and digits"""
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choices(lettersAndDigits, k=stringLength))


def update_panel_category(self, context):
    ui.unregister()
    ui.SESSION_PT_settings.bl_category = self.panel_category
    ui.register()


def update_ip(self, context):
    ip = IP_REGEX.search(self.ip)
    dns = HOSTNAME_REGEX.search(self.ip)

    if ip:
        self['ip'] = ip.group()
    elif dns:
        self['ip'] = dns.group()
    else:
        logging.error("Wrong IP format")
        self['ip'] = "127.0.0.1"


def update_port(self, context):
    max_port = self.port + 3

    if self.ipc_port < max_port and \
            self['ipc_port'] >= self.port:
        logging.error(
            "IPC Port in conflict with the port, assigning a random value")
        self['ipc_port'] = random.randrange(self.port+4, 10000)


def update_directory(self, context):
    new_dir = Path(self.cache_directory)
    if new_dir.exists() and any(Path(self.cache_directory).iterdir()):
        logging.error("The folder is not empty, choose another one.")
        self['cache_directory'] = environment.DEFAULT_CACHE_DIR
    elif not new_dir.exists():
        logging.info("Target cache folder doesn't exist, creating it.")
        os.makedirs(self.cache_directory, exist_ok=True)


def set_log_level(self, value):
    logging.getLogger().setLevel(value)


def get_log_level(self):
    return logging.getLogger().level


class ReplicatedDatablock(bpy.types.PropertyGroup):
    type_name: bpy.props.StringProperty()
    bl_name: bpy.props.StringProperty()
    bl_delay_refresh: bpy.props.FloatProperty()
    bl_delay_apply: bpy.props.FloatProperty()
    use_as_filter: bpy.props.BoolProperty(default=True)
    auto_push: bpy.props.BoolProperty(default=True)
    icon: bpy.props.StringProperty()


def set_sync_render_settings(self, value):
    self['sync_render_settings'] = value
    if session and bpy.context.scene.uuid and value:
        bpy.ops.session.apply('INVOKE_DEFAULT',
                              target=bpy.context.scene.uuid,
                              reset_dependencies=False)


def set_sync_active_camera(self, value):
    self['sync_active_camera'] = value

    if session and bpy.context.scene.uuid and value:
        bpy.ops.session.apply('INVOKE_DEFAULT',
                              target=bpy.context.scene.uuid,
                              reset_dependencies=False)


class ReplicationFlags(bpy.types.PropertyGroup):
    def get_sync_render_settings(self):
        return self.get('sync_render_settings', True)

    def get_sync_active_camera(self):
        return self.get('sync_active_camera', True)

    sync_render_settings: bpy.props.BoolProperty(
        name="Synchronize render settings",
        description="Synchronize render settings (eevee and cycles only)",
        default=False,
        set=set_sync_render_settings,
        get=get_sync_render_settings
    )
    sync_during_editmode: bpy.props.BoolProperty(
        name="Edit mode updates",
        description="Enable objects update in edit mode (! Impact performances !)",
        default=False
    )
    sync_active_camera: bpy.props.BoolProperty(
        name="Synchronize active camera",
        description="Synchronize the active camera",
        default=True,
        get=get_sync_active_camera,
        set=set_sync_active_camera
    )


class SessionPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    ip: bpy.props.StringProperty(
        name="ip",
        description='Distant host ip',
        default="127.0.0.1",
        update=update_ip)
    username: bpy.props.StringProperty(
        name="Username",
        default=f"user_{random_string_digits()}"
    )
    client_color: bpy.props.FloatVectorProperty(
        name="client_instance_color",
        subtype='COLOR',
        default=randomColor())
    port: bpy.props.IntProperty(
        name="port",
        description='Distant host port',
        default=5555
    )
    sync_flags: bpy.props.PointerProperty(
        type=ReplicationFlags
    )
    supported_datablocks: bpy.props.CollectionProperty(
        type=ReplicatedDatablock,
    )
    ipc_port: bpy.props.IntProperty(
        name="ipc_port",
        description='internal ttl port(only useful for multiple local instances)',
        default=random.randrange(5570, 70000),
        update=update_port,
    )
    init_method: bpy.props.EnumProperty(
        name='init_method',
        description='Init repo',
        items={
            ('EMPTY', 'an empty scene', 'start empty'),
            ('BLEND', 'current scenes', 'use current scenes')},
        default='BLEND')
    cache_directory: bpy.props.StringProperty(
        name="cache directory",
        subtype="DIR_PATH",
        default=environment.DEFAULT_CACHE_DIR,
        update=update_directory)
    connection_timeout: bpy.props.IntProperty(
        name='connection timeout',
        description='connection timeout before disconnection',
        default=1000
    )
    update_method: bpy.props.EnumProperty(
        name='update method',
        description='replication update method',
        items=[
            ('DEFAULT', "Default", "Default: Use threads to monitor databloc changes"),
            ('DEPSGRAPH', "Depsgraph",
             "Experimental: Use the blender dependency graph to trigger updates"),
        ],
    )
    # Replication update settings
    depsgraph_update_rate: bpy.props.IntProperty(
        name='depsgraph update rate',
        description='Dependency graph uppdate rate (milliseconds)',
        default=100
    )
    clear_memory_filecache: bpy.props.BoolProperty(
        name="Clear memory filecache",
        description="Remove filecache from memory",
        default=False
    )
    # for UI
    category: bpy.props.EnumProperty(
        name="Category",
        description="Preferences Category",
        items=[
            ('CONFIG', "Configuration", "Configuration of this add-on"),
            ('UPDATE', "Update", "Update this add-on"),
        ],
        default='CONFIG'
    )
    logging_level: bpy.props.EnumProperty(
        name="Log level",
        description="Log verbosity level",
        items=[
            ('ERROR', "error", "show only errors",  logging.ERROR),
            ('WARNING', "warning", "only show warnings and errors", logging.WARNING),
            ('INFO', "info", "default level", logging.INFO),
            ('DEBUG', "debug", "show all logs", logging.DEBUG),
        ],
        default='INFO',
        set=set_log_level,
        get=get_log_level
    )
    presence_hud_scale: bpy.props.FloatProperty(
        name="Text scale",
        description="Adjust the session widget text scale",
        min=7,
        max=90,
        default=25,
    )
    presence_hud_hpos: bpy.props.FloatProperty(
        name="Horizontal position",
        description="Adjust the session widget horizontal position",
        min=1,
        max=90,
        default=1,
        step=1,
        subtype='PERCENTAGE',
    )
    presence_hud_vpos: bpy.props.FloatProperty(
        name="Vertical position",
        description="Adjust the session widget vertical position",
        min=1,
        max=94,
        default=1,
        step=1,
        subtype='PERCENTAGE',
    )
    conf_session_identity_expanded: bpy.props.BoolProperty(
        name="Identity",
        description="Identity",
        default=True
    )
    conf_session_net_expanded: bpy.props.BoolProperty(
        name="Net",
        description="net",
        default=True
    )
    conf_session_hosting_expanded: bpy.props.BoolProperty(
        name="Rights",
        description="Rights",
        default=False
    )
    conf_session_timing_expanded: bpy.props.BoolProperty(
        name="timings",
        description="timings",
        default=False
    )
    conf_session_cache_expanded: bpy.props.BoolProperty(
        name="Cache",
        description="cache",
        default=False
    )
    conf_session_ui_expanded: bpy.props.BoolProperty(
        name="Interface",
        description="Interface",
        default=False
    )
    sidebar_advanced_rep_expanded: bpy.props.BoolProperty(
        name="sidebar_advanced_rep_expanded",
        description="sidebar_advanced_rep_expanded",
        default=False
    )
    sidebar_advanced_log_expanded: bpy.props.BoolProperty(
        name="sidebar_advanced_log_expanded",
        description="sidebar_advanced_log_expanded",
        default=False
    )
    sidebar_advanced_net_expanded: bpy.props.BoolProperty(
        name="sidebar_advanced_net_expanded",
        description="sidebar_advanced_net_expanded",
        default=False
    )
    sidebar_advanced_cache_expanded: bpy.props.BoolProperty(
        name="sidebar_advanced_cache_expanded",
        description="sidebar_advanced_cache_expanded",
        default=False
    )

    auto_check_update: bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False,
    )
    updater_intrval_months: bpy.props.IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_intrval_days: bpy.props.IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0,
        max=31
    )
    updater_intrval_hours: bpy.props.IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    updater_intrval_minutes: bpy.props.IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
    )

    # Custom panel
    panel_category: bpy.props.StringProperty(
        description="Choose a name for the category of the panel",
        default="Multiuser",
        update=update_panel_category)

    def draw(self, context):
        layout = self.layout

        layout.row().prop(self, "category", expand=True)

        if self.category == 'CONFIG':
            grid = layout.column()

            # USER INFORMATIONS
            box = grid.box()
            box.prop(
                self, "conf_session_identity_expanded", text="User information",
                icon=get_expanded_icon(self.conf_session_identity_expanded),
                emboss=False)
            if self.conf_session_identity_expanded:
                box.row().prop(self, "username", text="name")
                box.row().prop(self, "client_color", text="color")

            # NETWORK SETTINGS
            box = grid.box()
            box.prop(
                self, "conf_session_net_expanded", text="Networking",
                icon=get_expanded_icon(self.conf_session_net_expanded),
                emboss=False)

            if self.conf_session_net_expanded:
                box.row().prop(self, "ip", text="Address")
                row = box.row()
                row.label(text="Port:")
                row.prop(self, "port", text="")
                row = box.row()
                row.label(text="Init the session from:")
                row.prop(self, "init_method", text="")
                row = box.row()
                row.label(text="Update method:")
                row.prop(self, "update_method", text="")

                table = box.box()
                table.row().prop(
                    self, "conf_session_timing_expanded", text="Refresh rates",
                    icon=get_expanded_icon(self.conf_session_timing_expanded),
                    emboss=False)

                if self.conf_session_timing_expanded:
                    line = table.row()
                    line.label(text=" ")
                    line.separator()
                    line.label(text="refresh (sec)")
                    line.label(text="apply (sec)")

                    for item in self.supported_datablocks:
                        line = table.row(align=True)
                        line.label(text="", icon=item.icon)
                        line.prop(item, "bl_delay_refresh", text="")
                        line.prop(item, "bl_delay_apply", text="")
            # HOST SETTINGS
            box = grid.box()
            box.prop(
                self, "conf_session_hosting_expanded", text="Hosting",
                icon=get_expanded_icon(self.conf_session_hosting_expanded),
                emboss=False)
            if self.conf_session_hosting_expanded:
                row = box.row()
                row.label(text="Init the session from:")
                row.prop(self, "init_method", text="")

            # CACHE SETTINGS
            box = grid.box()
            box.prop(
                self, "conf_session_cache_expanded", text="Cache",
                icon=get_expanded_icon(self.conf_session_cache_expanded),
                emboss=False)
            if self.conf_session_cache_expanded:
                box.row().prop(self, "cache_directory", text="Cache directory")
                box.row().prop(self, "clear_memory_filecache", text="Clear memory filecache")

            # INTERFACE SETTINGS
            box = grid.box()
            box.prop(
                self, "conf_session_ui_expanded", text="Interface",
                icon=get_expanded_icon(self.conf_session_ui_expanded),
                emboss=False)
            if self.conf_session_ui_expanded:
                box.row().prop(self, "panel_category", text="Panel category", expand=True)
                row = box.row()
                row.label(text="Session widget:")

                col = box.column(align=True)
                col.prop(self, "presence_hud_scale", expand=True)
                

                col.prop(self, "presence_hud_hpos", expand=True)
                col.prop(self, "presence_hud_vpos", expand=True)

        if self.category == 'UPDATE':
            from . import addon_updater_ops
            addon_updater_ops.update_settings_ui(self, context)

    def generate_supported_types(self):
        self.supported_datablocks.clear()

        for type in bl_types.types_to_register():
            new_db = self.supported_datablocks.add()

            type_module = getattr(bl_types, type)
            type_impl_name = f"Bl{type.split('_')[1].capitalize()}"
            type_module_class = getattr(type_module, type_impl_name)

            new_db.name = type_impl_name
            new_db.type_name = type_impl_name
            new_db.bl_delay_refresh = type_module_class.bl_delay_refresh
            new_db.bl_delay_apply = type_module_class.bl_delay_apply
            new_db.use_as_filter = True
            new_db.icon = type_module_class.bl_icon
            new_db.auto_push = type_module_class.bl_automatic_push
            new_db.bl_name = type_module_class.bl_id


def client_list_callback(scene, context):
    from . import operators

    items = [(RP_COMMON, RP_COMMON, "")]

    username = get_preferences().username

    if session:
        client_ids = session.online_users.keys()
        for id in client_ids:
            name_desc = id
            if id == username:
                name_desc += " (self)"

            items.append((id, name_desc, ""))

    return items


class SessionUser(bpy.types.PropertyGroup):
    """Session User

    Blender user information property 
    """
    username: bpy.props.StringProperty(name="username")
    current_frame: bpy.props.IntProperty(name="current_frame")


class SessionProps(bpy.types.PropertyGroup):
    session_mode: bpy.props.EnumProperty(
        name='session_mode',
        description='session mode',
        items={
            ('HOST', 'HOST', 'host a session'),
            ('CONNECT', 'JOIN', 'connect to a session')},
        default='CONNECT')
    clients: bpy.props.EnumProperty(
        name="clients",
        description="client enum",
        items=client_list_callback)
    enable_presence: bpy.props.BoolProperty(
        name="Presence overlay",
        description='Enable overlay drawing module',
        default=True,
    )
    presence_show_selected: bpy.props.BoolProperty(
        name="Show selected objects",
        description='Enable selection overlay ',
        default=True,
    )
    presence_show_user: bpy.props.BoolProperty(
        name="Show users",
        description='Enable user overlay ',
        default=True,
    )
    presence_show_far_user: bpy.props.BoolProperty(
        name="Show users on different scenes",
        description="Show user on different scenes",
        default=False,
    )
    presence_show_session_status: bpy.props.BoolProperty(
        name="Show session status ",
        description="Show session status on the viewport",
        default=True,
    )
    filter_owned: bpy.props.BoolProperty(
        name="filter_owned",
        description='Show only owned datablocks',
        default=True
    )
    admin: bpy.props.BoolProperty(
        name="admin",
        description='Connect as admin',
        default=False
    )
    password: bpy.props.StringProperty(
        name="password",
        default=random_string_digits(),
        description='Session password',
        subtype='PASSWORD'
    )
    internet_ip: bpy.props.StringProperty(
        name="internet ip",
        default="no found",
        description='Internet interface ip',
    )
    user_snap_running: bpy.props.BoolProperty(
        default=False
    )
    time_snap_running: bpy.props.BoolProperty(
        default=False
    )
    is_host: bpy.props.BoolProperty(
        default=False
    )


classes = (
    SessionUser,
    SessionProps,
    ReplicationFlags,
    ReplicatedDatablock,
    SessionPrefs,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    prefs = bpy.context.preferences.addons[__package__].preferences
    if len(prefs.supported_datablocks) == 0:
        logging.debug('Generating bl_types preferences')
        prefs.generate_supported_types()


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
