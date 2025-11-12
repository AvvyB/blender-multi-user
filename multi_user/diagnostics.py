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
import sys
from replication.interface import session
from replication.constants import STATE_ACTIVE


class MULTIUSER_OT_show_diagnostics(bpy.types.Operator):
    """Show diagnostic information"""
    bl_idname = "multiuser.show_diagnostics"
    bl_label = "Diagnostics"
    bl_description = "Show version and connection information"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=500)

    def draw(self, context):
        from . import utils
        layout = self.layout

        layout.label(text="Multi-User Diagnostics", icon='INFO')
        layout.separator()

        # Version info
        box = layout.box()
        box.label(text="Version Information:", icon='PREFERENCES')
        col = box.column(align=True)

        addon_version = utils.get_version()
        col.label(text=f"Addon Version: {addon_version}")

        # Replication version
        try:
            import replication
            replication_version = getattr(replication, '__version__', 'Unknown')
            col.label(text=f"Replication Library: {replication_version}")
        except:
            col.label(text="Replication Library: Not found", icon='ERROR')

        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        col.label(text=f"Python Version: {python_version}")

        # Blender version
        blender_version = f"{bpy.app.version_string}"
        col.label(text=f"Blender Version: {blender_version}")

        layout.separator()

        # Connection info
        if session and session.state == STATE_ACTIVE:
            box = layout.box()
            box.label(text="Connection Status:", icon='LINKED')
            col = box.column(align=True)

            settings = utils.get_preferences()
            col.label(text=f"Username: {settings.username}")
            col.label(text=f"Connected: Yes")
            col.label(text=f"Online Users: {len(session.online_users)}")

            # List users
            if session.online_users:
                col.separator()
                col.label(text="Connected Users:")
                for username in session.online_users.keys():
                    col.label(text=f"  • {username}", icon='USER')
        else:
            box = layout.box()
            box.label(text="Not Connected", icon='UNLINKED')

        layout.separator()

        # Dependencies
        box = layout.box()
        box.label(text="Dependencies:", icon='PACKAGE')
        col = box.column(align=True)

        deps = [
            ('zmq', 'ZeroMQ'),
            ('deepdiff', 'DeepDiff'),
            ('orderly_set', 'OrderlySet'),
        ]

        for module_name, display_name in deps:
            try:
                module = __import__(module_name)
                version = getattr(module, '__version__', 'Installed')
                col.label(text=f"{display_name}: {version}", icon='CHECKMARK')
            except ImportError:
                col.label(text=f"{display_name}: Missing", icon='ERROR')


classes = (
    MULTIUSER_OT_show_diagnostics,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
