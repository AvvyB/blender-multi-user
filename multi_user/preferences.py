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

from . import utils, bl_types, environment, addon_updater_ops, presence

logger = logging.getLogger(__name__)

def randomColor():
    """Generate a random color """
    r = random.random()
    v = random.random()
    b = random.random()
    return [r, v, b]


def random_string_digits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choices(lettersAndDigits, k=stringLength))
    

class ReplicatedDatablock(bpy.types.PropertyGroup):
    type_name: bpy.props.StringProperty()
    bl_name: bpy.props.StringProperty()
    bl_delay_refresh: bpy.props.FloatProperty()
    bl_delay_apply: bpy.props.FloatProperty()
    use_as_filter: bpy.props.BoolProperty(default=True)
    auto_push: bpy.props.BoolProperty(default=True)
    icon: bpy.props.StringProperty()


class ReplicationFlags(bpy.types.PropertyGroup):
    sync_render_settings: bpy.props.BoolProperty(
        name="Synchronize render settings",
        description="Synchronize render settings (eevee and cycles only)",
        default=True)


class SessionPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    ip: bpy.props.StringProperty(
        name="ip",
        description='Distant host ip',
        default="127.0.0.1")
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
        description='internal ttl port(only usefull for multiple local instances)',
        default=5561
    )
    start_empty: bpy.props.BoolProperty(
        name="start_empty",
        default=False
    )
    right_strategy: bpy.props.EnumProperty(
        name='right_strategy',
        description='right strategy',
        items={
            ('STRICT', 'strict', 'strict right repartition'),
            ('COMMON', 'common', 'relaxed right repartition')},
        default='COMMON')
    cache_directory: bpy.props.StringProperty(
        name="cache directory",
        subtype="DIR_PATH",
        default=environment.DEFAULT_CACHE_DIR)
    # for UI
    category: bpy.props.EnumProperty(
        name="Category",
        description="Preferences Category",
        items=[
            ('CONFIG', "Configuration", "Configuration about this add-on"),
            ('UPDATE', "Update", "Update this add-on"),
        ],
        default='CONFIG'
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

    def draw(self, context):
        layout = self.layout

        layout.row().prop(self, "category", expand=True)
        
        if self.category == 'CONFIG':
            grid = layout.column()
            
            # USER INFORMATIONS
            box = grid.box()
            box.prop(
                self, "conf_session_identity_expanded", text="User informations",
                icon='DISCLOSURE_TRI_DOWN' if self.conf_session_identity_expanded
                else 'DISCLOSURE_TRI_RIGHT', emboss=False)
            if self.conf_session_identity_expanded:
                box.row().prop(self, "username", text="name")
                box.row().prop(self, "client_color", text="color")

            # NETWORK SETTINGS
            box = grid.box()
            box.prop(
                self, "conf_session_net_expanded", text="Netorking",
                icon='DISCLOSURE_TRI_DOWN' if self.conf_session_net_expanded
                else 'DISCLOSURE_TRI_RIGHT', emboss=False)

            if self.conf_session_net_expanded:
                box.row().prop(self, "ip", text="Address")
                row = box.row()
                row.label(text="Port:")
                row.prop(self, "port", text="Address")
                row = box.row()
                row.label(text="Start with an empty scene:")
                row.prop(self, "start_empty", text="")

                table = box.box()
                table.row().prop(
                    self, "conf_session_timing_expanded", text="Refresh rates",
                    icon='DISCLOSURE_TRI_DOWN' if self.conf_session_timing_expanded
                    else 'DISCLOSURE_TRI_RIGHT', emboss=False)
                
                if self.conf_session_timing_expanded:
                    line = table.row()
                    line.label(text=" ")
                    line.separator()
                    line.label(text="refresh (sec)")
                    line.label(text="apply (sec)")

                    for item in self.supported_datablocks:
                        line =  table.row(align=True)
                        line.label(text="", icon=item.icon)
                        line.prop(item, "bl_delay_refresh", text="")
                        line.prop(item, "bl_delay_apply", text="")
            # HOST SETTINGS
            box = grid.box()
            box.prop(
                self, "conf_session_hosting_expanded", text="Hosting",
                icon='DISCLOSURE_TRI_DOWN' if self.conf_session_hosting_expanded
                else 'DISCLOSURE_TRI_RIGHT', emboss=False)
            if self.conf_session_hosting_expanded:
                box.row().prop(self, "right_strategy", text="Right model")
                row = box.row()
                row.label(text="Start with an empty scene:")
                row.prop(self, "start_empty", text="")
            
            # CACHE SETTINGS
            box = grid.box()
            box.prop(
                self, "conf_session_cache_expanded", text="Cache",
                icon='DISCLOSURE_TRI_DOWN' if self.conf_session_cache_expanded
                else 'DISCLOSURE_TRI_RIGHT', emboss=False)
            if self.conf_session_cache_expanded:
                box.row().prop(self, "cache_directory", text="Cache directory")

        if self.category == 'UPDATE':
            from . import addon_updater_ops
            addon_updater_ops.update_settings_ui_condensed(self, context)

    def generate_supported_types(self):
        self.supported_datablocks.clear()

        for type in bl_types.types_to_register():
            new_db = self.supported_datablocks.add()

            type_module = getattr(bl_types, type)
            type_impl_name = "Bl{}".format(type.split('_')[1].capitalize())
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

    username = utils.get_preferences().username
    cli = operators.client
    if cli:
        client_ids = cli.online_users.keys()
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
    is_admin: bpy.props.BoolProperty(
        name="is_admin",
        default=False
        )
    session_mode: bpy.props.EnumProperty(
        name='session_mode',
        description='session mode',
        items={
            ('HOST', 'hosting', 'host a session'),
            ('CONNECT', 'connexion', 'connect to a session')},
        default='HOST')
    clients: bpy.props.EnumProperty(
        name="clients",
        description="client enum",
        items=client_list_callback)
    enable_presence: bpy.props.BoolProperty(
        name="Presence overlay",
        description='Enable overlay drawing module',
        default=True,
        update=presence.update_presence
        )
    presence_show_selected: bpy.props.BoolProperty(
        name="Show selected objects",
        description='Enable selection overlay ',
        default=True,
        update=presence.update_overlay_settings
    )
    presence_show_user: bpy.props.BoolProperty(
        name="Show users",
        description='Enable user overlay ',
        default=True,
        update=presence.update_overlay_settings
        )
    presence_show_far_user: bpy.props.BoolProperty(
        name="Show different scenes",
        description="Show user on different scenes",
        default=False,
        update=presence.update_overlay_settings
        )
    filter_owned: bpy.props.BoolProperty(
        name="filter_owned",
        description='Show only owned datablocks',
        default=True
    )
    user_snap_running: bpy.props.BoolProperty(
        default=False
    )
    time_snap_running: bpy.props.BoolProperty(
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
        logger.info('Generating bl_types preferences')
        prefs.generate_supported_types()


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
