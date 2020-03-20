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


bl_info = {
    "name": "Multi-User",
    "author": "Swann Martinez",
    "version": (0, 0, 3),
    "description": "Enable real-time collaborative workflow inside blender",
    "blender": (2, 80, 0),
    "location": "3D View > Sidebar > Multi-User tab",
    "warning": "Unstable addon, use it at your own risks",
    "category": "Collaboration",
    "doc_url": "https://multi-user.readthedocs.io/en/develop/index.html",
    "wiki_url": "https://multi-user.readthedocs.io/en/develop/index.html",
    "tracker_url": "https://gitlab.com/slumber/multi-user/issues",
    "support": "COMMUNITY"
}


import logging
import os
import random
import sys

import bpy
from bpy.app.handlers import persistent

from . import environment, utils, presence, preferences
from .libs.replication.replication.constants import  RP_COMMON


# TODO: remove dependency as soon as replication will be installed as a module
DEPENDENCIES = {
    ("zmq","zmq"),
    ("jsondiff","jsondiff")
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

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
)

libs = os.path.dirname(os.path.abspath(__file__))+"\\libs\\replication\\replication"

def register():
    if libs not in sys.path:
        sys.path.append(libs)
    
    environment.setup(DEPENDENCIES,bpy.app.binary_path_python)

    from . import presence
    from . import operators
    from . import ui
    from . import preferences
    from . import addon_updater_ops

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.session = bpy.props.PointerProperty(
        type=SessionProps)
    bpy.types.ID.uuid = bpy.props.StringProperty(default="")
    bpy.types.WindowManager.online_users = bpy.props.CollectionProperty(
        type=SessionUser
    )
    bpy.types.WindowManager.user_index = bpy.props.IntProperty()

    preferences.register()
    addon_updater_ops.register(bl_info)
    presence.register()
    operators.register()
    ui.register()

def unregister():
    from . import presence
    from . import operators
    from . import ui
    from . import preferences
    from . import addon_updater_ops

    presence.unregister()
    addon_updater_ops.unregister()
    ui.unregister()
    operators.unregister()
    preferences.unregister()
    del bpy.types.WindowManager.session

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
