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
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/AvvyB/blender-multi-user/refs/heads/master/version.json"
CHECK_INTERVAL_DAYS = 1  # Check for updates daily
GITHUB_RELEASES_API = "https://api.github.com/repos/AvvyB/blender-multi-user/releases/latest"

class UpdateChecker:
    """Checks for extension updates from a remote source"""

    def __init__(self):
        self.latest_version = None
        self.download_url = None
        self.update_available = False
        self.last_check_time = None
        self.checking = False
        self.downloading = False
        self.download_progress = 0.0

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
        """Check if a newer version is available on GitHub"""
        try:
            # Fetch latest release info from GitHub API
            req = urllib.request.Request(GITHUB_RELEASES_API)
            req.add_header('Accept', 'application/vnd.github.v3+json')

            with urllib.request.urlopen(req, timeout=10) as response:
                release_data = json.loads(response.read().decode())

            # Parse remote version from tag (e.g., "v0.8.1" or "0.8.1")
            tag_name = release_data.get('tag_name', '0.0.0')
            remote_version_str = tag_name.lstrip('v')
            remote_version = tuple(map(int, remote_version_str.split('.')))

            # Find the .zip asset in the release
            assets = release_data.get('assets', [])
            self.download_url = None

            for asset in assets:
                if asset['name'].endswith('.zip') and 'multi_user' in asset['name'].lower():
                    self.download_url = asset['browser_download_url']
                    break

            # If no asset found, try to construct URL from tag
            if not self.download_url and tag_name:
                self.download_url = f"https://github.com/AvvyB/blender-multi-user/releases/download/{tag_name}/multi_user-{remote_version_str}.zip"

            # Compare versions
            installed_version = self.get_installed_version()

            self.latest_version = remote_version_str
            self.update_available = remote_version > installed_version
            self.last_check_time = datetime.now()

            logging.info(f"Update check: Installed={installed_version}, Latest={remote_version}, Available={self.update_available}")
            if self.download_url:
                logging.info(f"Download URL: {self.download_url}")

            return self.update_available

        except Exception as e:
            logging.error(f"Update check failed: {e}")
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
    """Download and install the latest Multi-User update automatically"""
    bl_idname = "multiuser.download_update"
    bl_label = "Install Update"
    bl_description = "Automatically download and install the latest version"

    _timer = None
    _thread = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            # Check if download/install is complete
            if not update_checker.downloading:
                self.cancel(context)
                return {'FINISHED'}

            # Force redraw to show progress
            context.area.tag_redraw() if context.area else None

        return {'PASS_THROUGH'}

    def execute(self, context):
        if not update_checker.download_url:
            self.report({'ERROR'}, "No download URL available. Please check for updates first.")
            return {'CANCELLED'}

        if update_checker.downloading:
            self.report({'WARNING'}, "Update already in progress")
            return {'CANCELLED'}

        # Start download and install in background
        def download_and_install():
            try:
                update_checker.downloading = True
                update_checker.download_progress = 0.0

                logging.info(f"Downloading update from: {update_checker.download_url}")

                # Create temp directory for download
                temp_dir = Path(tempfile.mkdtemp(prefix="multiuser_update_"))
                zip_path = temp_dir / f"multi_user-{update_checker.latest_version}.zip"

                # Download with progress tracking
                def download_progress(block_num, block_size, total_size):
                    if total_size > 0:
                        update_checker.download_progress = (block_num * block_size) / total_size
                        logging.debug(f"Download progress: {update_checker.download_progress * 100:.1f}%")

                urllib.request.urlretrieve(
                    update_checker.download_url,
                    zip_path,
                    reporthook=download_progress
                )

                logging.info(f"Download complete: {zip_path}")
                update_checker.download_progress = 1.0

                # Install the extension using Blender's extension system
                # Note: This requires Blender 4.3+ extension system
                try:
                    # Use bpy.ops to install extension
                    # This will be called from main thread via timer
                    def install_extension():
                        try:
                            # Remove old version first
                            logging.info("Removing old version...")
                            bpy.ops.preferences.extension_remove(module='multi_user')

                            # Install new version
                            logging.info(f"Installing new version from {zip_path}")
                            bpy.ops.preferences.extension_install(filepath=str(zip_path))

                            # Clean up temp files
                            shutil.rmtree(temp_dir, ignore_errors=True)

                            logging.info("Update installed successfully!")
                            update_checker.update_available = False

                            # Schedule Blender restart prompt
                            def show_restart_prompt():
                                bpy.ops.multiuser.restart_prompt('INVOKE_DEFAULT')
                                return None

                            bpy.app.timers.register(show_restart_prompt, first_interval=0.5)

                        except Exception as e:
                            logging.error(f"Installation failed: {e}")
                            # Clean up on error
                            shutil.rmtree(temp_dir, ignore_errors=True)

                        finally:
                            update_checker.downloading = False

                    # Schedule installation on main thread
                    bpy.app.timers.register(install_extension, first_interval=0.1)

                except Exception as e:
                    logging.error(f"Failed to schedule installation: {e}")
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    update_checker.downloading = False

            except Exception as e:
                logging.error(f"Download failed: {e}")
                update_checker.downloading = False
                # Show error to user
                def show_error():
                    bpy.ops.multiuser.update_error('INVOKE_DEFAULT', message=str(e))
                    return None
                bpy.app.timers.register(show_error, first_interval=0.1)

        # Start download thread
        self._thread = threading.Thread(target=download_and_install, daemon=True)
        self._thread.start()

        self.report({'INFO'}, "Downloading update...")

        # Register modal timer for progress updates
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None


class MULTIUSER_PT_update_notification(bpy.types.Panel):
    """Panel that shows update notification"""
    bl_label = "Update Available"
    bl_idname = "MULTIUSER_PT_update_notification"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 12

    @classmethod
    def poll(cls, context):
        # Show if update is available or currently downloading
        return update_checker.update_available or update_checker.downloading

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)

        if update_checker.downloading:
            # Show download progress
            col.label(text="Downloading Update...", icon='IMPORT')
            col.label(text=f"Version: {update_checker.latest_version}")
            col.separator()

            # Progress bar
            progress = update_checker.download_progress
            row = col.row()
            row.scale_y = 1.5
            row.prop(context.window_manager, "dummy_prop", text=f"{int(progress * 100)}%", slider=True, emboss=False)

            col.label(text="Installing after download completes...")

        else:
            # Show update notification
            col.label(text="Multi-User Update Available!", icon='INFO')
            col.label(text=f"New version: {update_checker.latest_version}")
            col.separator()

            row = col.row(align=True)
            row.operator("multiuser.download_update", text="Install Update", icon='IMPORT')
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


class MULTIUSER_OT_restart_prompt(bpy.types.Operator):
    """Prompt user to restart Blender after update"""
    bl_idname = "multiuser.restart_prompt"
    bl_label = "Update Installed - Restart Required"
    bl_description = "Update installed successfully, restart Blender to use new version"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Multi-User has been updated successfully!", icon='CHECKMARK')
        layout.separator()
        layout.label(text="Please restart Blender to use the new version.")
        layout.label(text=f"New version: {update_checker.latest_version}")


class MULTIUSER_OT_update_error(bpy.types.Operator):
    """Show update error message"""
    bl_idname = "multiuser.update_error"
    bl_label = "Update Failed"
    bl_description = "Update installation failed"

    message: bpy.props.StringProperty(default="Unknown error")

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Failed to install update", icon='ERROR')
        layout.separator()
        layout.label(text="Error:")

        # Split long error messages
        words = self.message.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 > 60:
                layout.label(text=line)
                line = word
            else:
                line = line + " " + word if line else word
        if line:
            layout.label(text=line)

        layout.separator()
        layout.label(text="Please download manually from GitHub:")
        layout.operator("wm.url_open", text="Open GitHub Releases", icon='URL').url = "https://github.com/AvvyB/blender-multi-user/releases/latest"


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
    MULTIUSER_OT_restart_prompt,
    MULTIUSER_OT_update_error,
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
