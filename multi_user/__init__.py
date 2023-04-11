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
    "version": (0, 5, 8),
    "description": "Enable real-time collaborative workflow inside blender",
    "blender": (2, 82, 0),
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

from . import environment


module_error_msg = "Insufficient rights to install the multi-user \
                dependencies, aunch blender with administrator rights."


def register():
    # Setup logging policy
    logging.basicConfig(
        format='%(asctime)s CLIENT %(levelname)-8s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.INFO)

    try:
        environment.register()

        from . import presence
        from . import operators
        from . import handlers
        from . import ui
        from . import icons
        from . import preferences
        from . import addon_updater_ops

        preferences.register()
        addon_updater_ops.register(bl_info)
        presence.register()
        operators.register()
        handlers.register()
        ui.register()
        icons.register()
    except ModuleNotFoundError as e:
        raise Exception(module_error_msg)
        logging.error(module_error_msg)
 
    bpy.types.WindowManager.session = bpy.props.PointerProperty(
        type=preferences.SessionProps)
    bpy.types.ID.uuid = bpy.props.StringProperty(
        default="",
        options={'HIDDEN', 'SKIP_SAVE'})
    bpy.types.WindowManager.online_users = bpy.props.CollectionProperty(
        type=preferences.SessionUser
    )
    bpy.types.WindowManager.user_index = bpy.props.IntProperty()
    bpy.types.WindowManager.server_index = bpy.props.IntProperty()
    bpy.types.TOPBAR_MT_file_import.append(operators.menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(operators.menu_func_export)


def unregister():
    from . import presence
    from . import operators
    from . import handlers
    from . import ui
    from . import icons
    from . import preferences
    from . import addon_updater_ops

    bpy.types.TOPBAR_MT_file_import.remove(operators.menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(operators.menu_func_export)

    presence.unregister()
    addon_updater_ops.unregister()
    ui.unregister()
    icons.unregister()
    handlers.unregister()
    operators.unregister()
    preferences.unregister()

    del bpy.types.WindowManager.session
    del bpy.types.ID.uuid
    del bpy.types.WindowManager.online_users
    del bpy.types.WindowManager.user_index
    del bpy.types.WindowManager.server_index

    environment.unregister()
