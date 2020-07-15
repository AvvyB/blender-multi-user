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

from . import environment, utils


# TODO: remove dependency as soon as replication will be installed as a module
DEPENDENCIES = {
    ("replication", '0.0.17'),
    ("deepdiff", '5.0.1'),
}


def register():
    # Setup logging policy
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    try:
        environment.setup(DEPENDENCIES, bpy.app.binary_path_python)
    except ModuleNotFoundError:
        logging.fatal("Fail to install multi-user dependencies, try to execute blender with admin rights.")
        return
        
    from . import presence
    from . import operators
    from . import ui
    from . import preferences
    from . import addon_updater_ops

    preferences.register()
    addon_updater_ops.register(bl_info)
    presence.register()
    operators.register()
    ui.register()

    bpy.types.WindowManager.session = bpy.props.PointerProperty(
        type=preferences.SessionProps)
    bpy.types.ID.uuid = bpy.props.StringProperty(
        default="",
        options={'HIDDEN', 'SKIP_SAVE'})
    bpy.types.WindowManager.online_users = bpy.props.CollectionProperty(
        type=preferences.SessionUser
    )
    bpy.types.WindowManager.user_index = bpy.props.IntProperty()

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
    del bpy.types.ID.uuid
    del bpy.types.WindowManager.online_users
    del bpy.types.WindowManager.user_index
