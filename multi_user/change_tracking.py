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
import time
from datetime import datetime
from collections import deque
from replication.interface import session
from replication.constants import STATE_ACTIVE


# Global change history storage
class ChangeHistory:
    """Track changes made by users (git blame-like)"""
    def __init__(self, max_history=1000):
        self.changes = deque(maxlen=max_history)  # Limited history
        self.object_history = {}  # object_name -> [changes]

    def add_change(self, object_name, property_name, old_value, new_value, username, timestamp=None):
        """Record a change"""
        if timestamp is None:
            timestamp = time.time()

        change = {
            'object': object_name,
            'property': property_name,
            'old_value': str(old_value),
            'new_value': str(new_value),
            'user': username,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        }

        self.changes.append(change)

        # Track per-object history
        if object_name not in self.object_history:
            self.object_history[object_name] = []
        self.object_history[object_name].append(change)

    def get_object_changes(self, object_name, limit=50):
        """Get change history for an object"""
        return self.object_history.get(object_name, [])[-limit:]

    def get_recent_changes(self, limit=50):
        """Get most recent changes across all objects"""
        return list(self.changes)[-limit:]

    def get_user_changes(self, username, limit=50):
        """Get all changes by a specific user"""
        user_changes = [c for c in self.changes if c['user'] == username]
        return user_changes[-limit:]

    def clear(self):
        """Clear all history"""
        self.changes.clear()
        self.object_history.clear()


# Global instance
change_history = ChangeHistory()


# Undo/Redo System
class UndoRedoManager:
    """Collaborative undo/redo system"""
    def __init__(self, max_undo=50):
        self.undo_stack = deque(maxlen=max_undo)
        self.redo_stack = deque(maxlen=max_undo)
        self.enabled = True

    def push_undo(self, action_data):
        """Push an action to undo stack"""
        if not self.enabled:
            return

        self.undo_stack.append(action_data)
        # Clear redo stack when new action is performed
        self.redo_stack.clear()

    def undo(self):
        """Undo last action"""
        if not self.undo_stack:
            return None

        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        return action

    def redo(self):
        """Redo last undone action"""
        if not self.redo_stack:
            return None

        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        return action

    def can_undo(self):
        """Check if undo is available"""
        return len(self.undo_stack) > 0

    def can_redo(self):
        """Check if redo is available"""
        return len(self.redo_stack) > 0

    def clear(self):
        """Clear undo/redo history"""
        self.undo_stack.clear()
        self.redo_stack.clear()


# Global instance
undo_manager = UndoRedoManager()


# Operators
class MULTIUSER_OT_show_change_history(bpy.types.Operator):
    """Show change history for selected object"""
    bl_idname = "multiuser.show_change_history"
    bl_label = "Change History"
    bl_description = "View who made changes to this object"

    @classmethod
    def poll(cls, context):
        return (session and session.state == STATE_ACTIVE and
                context.active_object is not None)

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=600)

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        layout.label(text=f"Change History: {obj.name}", icon='TIME')
        layout.separator()

        changes = change_history.get_object_changes(obj.name, limit=20)

        if not changes:
            layout.label(text="No changes recorded yet", icon='INFO')
        else:
            box = layout.box()
            col = box.column(align=True)

            for change in reversed(changes):  # Show newest first
                row = col.row()
                row.label(text=change['datetime'])
                row.label(text=change['user'], icon='USER')
                row.label(text=f"{change['property']}: {change['old_value']} → {change['new_value']}")
                col.separator()


class MULTIUSER_OT_show_recent_changes(bpy.types.Operator):
    """Show recent changes by all users"""
    bl_idname = "multiuser.show_recent_changes"
    bl_label = "Recent Changes"
    bl_description = "View recent changes made by all users"

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=700)

    def draw(self, context):
        layout = self.layout

        layout.label(text="Recent Changes (All Users)", icon='TIME')
        layout.separator()

        changes = change_history.get_recent_changes(limit=30)

        if not changes:
            layout.label(text="No changes recorded yet", icon='INFO')
        else:
            box = layout.box()
            col = box.column(align=True)

            for change in reversed(changes):  # Show newest first
                row = col.row()
                row.label(text=change['datetime'][:16])  # Date & time
                row.label(text=change['user'], icon='USER')
                row.label(text=change['object'][:20])  # Object name (truncated)
                row.label(text=change['property'][:15])  # Property name
                col.separator()


class MULTIUSER_OT_collaborative_undo(bpy.types.Operator):
    """Undo last collaborative action"""
    bl_idname = "multiuser.collaborative_undo"
    bl_label = "Collaborative Undo"
    bl_description = "Undo the last collaborative change"

    @classmethod
    def poll(cls, context):
        return (session and session.state == STATE_ACTIVE and
                undo_manager.can_undo())

    def execute(self, context):
        action = undo_manager.undo()
        if action:
            self.report({'INFO'}, f"Undid: {action.get('description', 'unknown action')}")
        else:
            self.report({'WARNING'}, "Nothing to undo")
        return {'FINISHED'}


class MULTIUSER_OT_collaborative_redo(bpy.types.Operator):
    """Redo last undone collaborative action"""
    bl_idname = "multiuser.collaborative_redo"
    bl_label = "Collaborative Redo"
    bl_description = "Redo the last undone collaborative change"

    @classmethod
    def poll(cls, context):
        return (session and session.state == STATE_ACTIVE and
                undo_manager.can_redo())

    def execute(self, context):
        action = undo_manager.redo()
        if action:
            self.report({'INFO'}, f"Redid: {action.get('description', 'unknown action')}")
        else:
            self.report({'WARNING'}, "Nothing to redo")
        return {'FINISHED'}


# UI Panel
class MULTIUSER_PT_change_tracking(bpy.types.Panel):
    """Panel for change tracking and history"""
    bl_label = "History"
    bl_idname = "MULTIUSER_PT_change_tracking"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Multi-User'
    bl_order = 3

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def draw(self, context):
        layout = self.layout

        # Undo/Redo section
        box = layout.box()
        box.label(text="Collaborative Undo/Redo:", icon='LOOP_BACK')
        col = box.column(align=True)

        row = col.row(align=True)
        row.scale_y = 1.2
        op = row.operator("multiuser.collaborative_undo", text="Undo", icon='LOOP_BACK')
        op.enabled = undo_manager.can_undo()
        op = row.operator("multiuser.collaborative_redo", text="Redo", icon='LOOP_FORWARDS')
        op.enabled = undo_manager.can_redo()

        col.label(text=f"{len(undo_manager.undo_stack)} actions available")

        layout.separator()

        # Change history section
        box = layout.box()
        box.label(text="Change History:", icon='TIME')
        col = box.column(align=True)
        col.scale_y = 1.1

        col.operator("multiuser.show_recent_changes", text="View Recent Changes", icon='TIME')

        if context.active_object:
            col.operator("multiuser.show_change_history",
                        text=f"History: {context.active_object.name[:20]}",
                        icon='OBJECT_DATA')
        else:
            col.enabled = False
            col.operator("multiuser.show_change_history",
                        text="Select Object to View History",
                        icon='INFO')


classes = (
    MULTIUSER_OT_show_change_history,
    MULTIUSER_OT_show_recent_changes,
    MULTIUSER_OT_collaborative_undo,
    MULTIUSER_OT_collaborative_redo,
    MULTIUSER_PT_change_tracking,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
