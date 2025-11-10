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
import json
import logging
import threading
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/multi-user/main/version.json"
CHECK_INTERVAL_DAYS = 1  # Check for updates daily

class UpdateChecker:
    """Checks for extension updates from a remote source"""

    def __init__(self):
        self.latest_version = None
        self.update_available = False
        self.last_check_time = None
        self.checking = False

    def get_installed_version(self):
        """Get the currently installed version"""
        from . import utils
        version_str = utils.get_version()
        try:
            # Convert "0.6.9" to tuple (0, 6, 9)
            return tuple(map(int, version_str.split('.')))
        except:
            return (0, 0, 0)

    def should_check_for_update(self):
        """Check if enough time has passed since last update check"""
        if self.last_check_time is None:
            return True

        elapsed = datetime.now() - self.last_check_time
        return elapsed > timedelta(days=CHECK_INTERVAL_DAYS)

    def check_for_updates_async(self, callback=None):
        """Check for updates in a background thread"""
        if self.checking:
            return

        def check_thread():
            try:
                self.checking = True
                self.check_for_updates()
                if callback:
                    callback(self.update_available, self.latest_version)
            finally:
                self.checking = False

        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()

    def check_for_updates(self):
        """Check if a newer version is available"""
        try:
            # Fetch version info from remote
            with urllib.request.urlopen(UPDATE_CHECK_URL, timeout=5) as response:
                data = json.loads(response.read().decode())

            # Parse remote version
            remote_version_str = data.get('version', '0.0.0')
            remote_version = tuple(map(int, remote_version_str.split('.')))

            # Compare versions
            installed_version = self.get_installed_version()

            self.latest_version = remote_version_str
            self.update_available = remote_version > installed_version
            self.last_check_time = datetime.now()

            logging.info(f"Update check: Installed={installed_version}, Latest={remote_version}, Available={self.update_available}")

            return self.update_available

        except Exception as e:
            logging.debug(f"Update check failed: {e}")
            return False


# Global update checker instance
update_checker = UpdateChecker()


class MULTIUSER_OT_check_updates(bpy.types.Operator):
    """Check for Multi-User extension updates"""
    bl_idname = "multiuser.check_updates"
    bl_label = "Check for Updates"
    bl_description = "Check if a newer version of Multi-User is available"

    def execute(self, context):
        def on_check_complete(available, version):
            if available:
                self.report({'INFO'}, f"Update available: v{version}")
            else:
                self.report({'INFO'}, "You're using the latest version")

        update_checker.check_for_updates_async(callback=on_check_complete)
        self.report({'INFO'}, "Checking for updates...")

        return {'FINISHED'}


class MULTIUSER_OT_download_update(bpy.types.Operator):
    """Download and install the latest Multi-User update"""
    bl_idname = "multiuser.download_update"
    bl_label = "Download Update"
    bl_description = "Download and install the latest version"

    def execute(self, context):
        self.report({'INFO'}, "Opening download page in browser...")

        # Open the releases page in browser
        import webbrowser
        webbrowser.open("https://github.com/YOUR_USERNAME/multi-user/releases/latest")

        return {'FINISHED'}


class MULTIUSER_PT_update_notification(bpy.types.Panel):
    """Panel that shows update notification"""
    bl_label = "Update Available"
    bl_idname = "MULTIUSER_PT_update_notification"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 12

    @classmethod
    def poll(cls, context):
        # Only show if update is available
        return update_checker.update_available

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)

        col.label(text="Multi-User Update Available!", icon='INFO')
        col.label(text=f"New version: {update_checker.latest_version}")
        col.separator()

        row = col.row(align=True)
        row.operator("multiuser.download_update", text="Download Update", icon='IMPORT')
        row.operator("multiuser.dismiss_update", text="Dismiss", icon='X')


class MULTIUSER_OT_dismiss_update(bpy.types.Operator):
    """Dismiss the update notification"""
    bl_idname = "multiuser.dismiss_update"
    bl_label = "Dismiss Update"
    bl_description = "Hide the update notification for now"

    def execute(self, context):
        update_checker.update_available = False
        self.report({'INFO'}, "Update notification dismissed")
        return {'FINISHED'}


# Startup handler to check for updates
@bpy.app.handlers.persistent
def check_updates_on_startup(dummy):
    """Check for updates when Blender starts"""
    if update_checker.should_check_for_update():
        def on_update_check(available, version):
            if available:
                logging.info(f"Multi-User update available: v{version}")

        # Delay check by 2 seconds to let Blender fully start
        bpy.app.timers.register(
            lambda: update_checker.check_for_updates_async(callback=on_update_check),
            first_interval=2.0
        )


classes = (
    MULTIUSER_OT_check_updates,
    MULTIUSER_OT_download_update,
    MULTIUSER_OT_dismiss_update,
    MULTIUSER_PT_update_notification,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register startup handler
    if check_updates_on_startup not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(check_updates_on_startup)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Unregister startup handler
    if check_updates_on_startup in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(check_updates_on_startup)
