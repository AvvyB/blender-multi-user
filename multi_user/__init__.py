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


import logging

import bpy

from . import presence
from . import operators
from . import handlers
from . import ui
from . import icons
from . import preferences
from . import update_checker
from . import scene_management
from . import change_tracking
from . import task_management
from . import chat_system


def register():
    # Setup logging policy
    logging.basicConfig(
        format="%(asctime)s CLIENT %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )

    preferences.register()
    presence.register()
    operators.register()
    handlers.register()
    ui.register()
    icons.register()
    update_checker.register()
    scene_management.register()
    change_tracking.register()
    task_management.register()
    chat_system.register()

    bpy.types.WindowManager.session = bpy.props.PointerProperty(
        type=preferences.SessionProps
    )
    bpy.types.ID.uuid = bpy.props.StringProperty(
        default="", options={"HIDDEN", "SKIP_SAVE"}
    )
    bpy.types.WindowManager.online_users = bpy.props.CollectionProperty(
        type=preferences.SessionUser
    )
    bpy.types.WindowManager.user_index = bpy.props.IntProperty()
    bpy.types.WindowManager.server_index = bpy.props.IntProperty()
    bpy.types.TOPBAR_MT_file_import.append(operators.menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(operators.menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(operators.menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(operators.menu_func_export)

    chat_system.unregister()
    task_management.unregister()
    change_tracking.unregister()
    scene_management.unregister()
    update_checker.unregister()
    presence.unregister()
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
