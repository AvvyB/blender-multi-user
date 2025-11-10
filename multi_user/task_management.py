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
import time
from replication.interface import session
from replication.constants import STATE_ACTIVE
from replication import porcelain


# Task storage
class Task:
    def __init__(self, title, description="", assigned_to="", status="todo", created_by="", object_name=""):
        self.id = str(time.time())
        self.title = title
        self.description = description
        self.assigned_to = assigned_to
        self.status = status  # todo, in_progress, done
        self.created_by = created_by
        self.created_at = time.time()
        self.object_name = object_name  # Optional: link to specific object

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'assigned_to': self.assigned_to,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'object_name': self.object_name
        }

    @staticmethod
    def from_dict(data):
        task = Task(
            title=data['title'],
            description=data.get('description', ''),
            assigned_to=data.get('assigned_to', ''),
            status=data.get('status', 'todo'),
            created_by=data.get('created_by', ''),
            object_name=data.get('object_name', '')
        )
        task.id = data['id']
        task.created_at = data.get('created_at', time.time())
        return task


class TaskManager:
    def __init__(self):
        self.tasks = {}  # task_id -> Task

    def add_task(self, task):
        self.tasks[task.id] = task
        self.sync_tasks()

    def remove_task(self, task_id):
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.sync_tasks()

    def update_task(self, task_id, **kwargs):
        if task_id in self.tasks:
            for key, value in kwargs.items():
                setattr(self.tasks[task_id], key, value)
            self.sync_tasks()

    def get_tasks(self, status=None, assigned_to=None):
        """Get filtered tasks"""
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]
        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]

        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def sync_tasks(self):
        """Sync tasks to server via metadata"""
        if session and session.state == STATE_ACTIVE:
            tasks_data = {tid: t.to_dict() for tid, t in self.tasks.items()}
            try:
                porcelain.update_user_metadata(session.repository, {
                    'tasks': json.dumps(tasks_data)
                })
            except Exception as e:
                print(f"Failed to sync tasks: {e}")

    def load_tasks_from_metadata(self):
        """Load tasks from server metadata"""
        if session and session.state == STATE_ACTIVE:
            for username, user_data in session.online_users.items():
                metadata = user_data.get('metadata', {})
                tasks_json = metadata.get('tasks')
                if tasks_json:
                    try:
                        tasks_data = json.loads(tasks_json)
                        for task_dict in tasks_data.values():
                            task = Task.from_dict(task_dict)
                            if task.id not in self.tasks:
                                self.tasks[task.id] = task
                    except:
                        pass

    def clear(self):
        self.tasks.clear()


# Global instance
task_manager = TaskManager()


# Operators
class MULTIUSER_OT_add_task(bpy.types.Operator):
    """Add a new task"""
    bl_idname = "multiuser.add_task"
    bl_label = "Add Task"
    bl_description = "Create a new task for the team"
    bl_options = {'REGISTER', 'UNDO'}

    title: bpy.props.StringProperty(
        name="Title",
        description="Task title",
        default="New Task"
    )

    description: bpy.props.StringProperty(
        name="Description",
        description="Task description",
        default=""
    )

    assigned_to: bpy.props.StringProperty(
        name="Assign To",
        description="Username to assign task to (leave empty for unassigned)",
        default=""
    )

    link_to_object: bpy.props.BoolProperty(
        name="Link to Active Object",
        description="Link this task to the currently selected object",
        default=False
    )

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "title")
        layout.prop(self, "description")
        layout.prop(self, "assigned_to")

        if context.active_object:
            layout.prop(self, "link_to_object")

    def execute(self, context):
        if not session or session.state != STATE_ACTIVE:
            self.report({'ERROR'}, "Not connected to a session")
            return {'CANCELLED'}

        from . import utils
        settings = utils.get_preferences()

        object_name = ""
        if self.link_to_object and context.active_object:
            object_name = context.active_object.name

        task = Task(
            title=self.title,
            description=self.description,
            assigned_to=self.assigned_to,
            created_by=settings.username,
            object_name=object_name
        )

        task_manager.add_task(task)

        self.report({'INFO'}, f"Task created: {self.title}")
        return {'FINISHED'}


class MULTIUSER_OT_update_task_status(bpy.types.Operator):
    """Update task status"""
    bl_idname = "multiuser.update_task_status"
    bl_label = "Update Status"
    bl_description = "Change task status"

    task_id: bpy.props.StringProperty()
    new_status: bpy.props.EnumProperty(
        items=[
            ('todo', "To Do", "Task not started"),
            ('in_progress', "In Progress", "Task being worked on"),
            ('done', "Done", "Task completed"),
        ]
    )

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def execute(self, context):
        task_manager.update_task(self.task_id, status=self.new_status)
        self.report({'INFO'}, f"Task status updated to {self.new_status}")
        return {'FINISHED'}


class MULTIUSER_OT_delete_task(bpy.types.Operator):
    """Delete a task"""
    bl_idname = "multiuser.delete_task"
    bl_label = "Delete Task"
    bl_description = "Remove this task"

    task_id: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def execute(self, context):
        task_manager.remove_task(self.task_id)
        self.report({'INFO'}, "Task deleted")
        return {'FINISHED'}


class MULTIUSER_OT_view_tasks(bpy.types.Operator):
    """View all tasks"""
    bl_idname = "multiuser.view_tasks"
    bl_label = "Task List"
    bl_description = "View all tasks in the session"

    filter_status: bpy.props.EnumProperty(
        name="Filter",
        items=[
            ('all', "All Tasks", "Show all tasks"),
            ('todo', "To Do", "Show only todo tasks"),
            ('in_progress', "In Progress", "Show only in-progress tasks"),
            ('done', "Done", "Show only completed tasks"),
        ],
        default='all'
    )

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def invoke(self, context, event):
        # Load latest tasks from metadata
        task_manager.load_tasks_from_metadata()
        return context.window_manager.invoke_popup(self, width=700)

    def draw(self, context):
        layout = self.layout

        layout.label(text="Task List", icon='PRESET')
        layout.prop(self, "filter_status", text="")
        layout.separator()

        # Get filtered tasks
        if self.filter_status == 'all':
            tasks = task_manager.get_tasks()
        else:
            tasks = task_manager.get_tasks(status=self.filter_status)

        if not tasks:
            layout.label(text="No tasks found", icon='INFO')
        else:
            for task in tasks:
                box = layout.box()
                col = box.column()

                # Title and status
                row = col.row()
                if task.status == 'done':
                    row.label(text=task.title, icon='CHECKMARK')
                elif task.status == 'in_progress':
                    row.label(text=task.title, icon='PLAY')
                else:
                    row.label(text=task.title, icon='DOT')

                # Details
                row = col.row()
                row.scale_y = 0.8
                if task.assigned_to:
                    row.label(text=f"Assigned: {task.assigned_to}", icon='USER')
                else:
                    row.label(text="Unassigned", icon='QUESTION')

                if task.object_name:
                    row.label(text=f"Object: {task.object_name}", icon='OBJECT_DATA')

                # Status buttons
                row = col.row(align=True)
                for status_key, status_label, status_icon in [
                    ('todo', "To Do", 'DOT'),
                    ('in_progress', "In Progress", 'PLAY'),
                    ('done', "Done", 'CHECKMARK')
                ]:
                    op = row.operator("multiuser.update_task_status", text=status_label, icon=status_icon)
                    op.task_id = task.id
                    op.new_status = status_key
                    if task.status == status_key:
                        op.enabled = False

                # Delete button
                op = col.operator("multiuser.delete_task", text="Delete", icon='TRASH')
                op.task_id = task.id

                col.separator()

    def execute(self, context):
        return {'FINISHED'}


# UI Panel
class MULTIUSER_PT_tasks(bpy.types.Panel):
    """Panel for task management"""
    bl_label = "Tasks"
    bl_idname = "MULTIUSER_PT_tasks"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Multi-User'
    bl_order = 2

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def draw(self, context):
        layout = self.layout

        # Add task button
        box = layout.box()
        box.label(text="Create Task:", icon='ADD')
        col = box.column(align=True)
        col.scale_y = 1.2
        col.operator("multiuser.add_task", text="New Task", icon='ADD')

        layout.separator()

        # View tasks
        box = layout.box()
        box.label(text="View Tasks:", icon='PRESET')
        col = box.column(align=True)
        col.scale_y = 1.1

        # Load latest tasks
        task_manager.load_tasks_from_metadata()

        # Count tasks by status
        todo_count = len(task_manager.get_tasks(status='todo'))
        in_progress_count = len(task_manager.get_tasks(status='in_progress'))
        done_count = len(task_manager.get_tasks(status='done'))

        col.operator("multiuser.view_tasks", text=f"All Tasks ({len(task_manager.tasks)})", icon='PRESET')

        row = col.row(align=True)
        row.scale_y = 0.9
        op = row.operator("multiuser.view_tasks", text=f"To Do ({todo_count})", icon='DOT')
        op.filter_status = 'todo'
        op = row.operator("multiuser.view_tasks", text=f"In Progress ({in_progress_count})", icon='PLAY')
        op.filter_status = 'in_progress'
        op = row.operator("multiuser.view_tasks", text=f"Done ({done_count})", icon='CHECKMARK')
        op.filter_status = 'done'


classes = (
    MULTIUSER_OT_add_task,
    MULTIUSER_OT_update_task_status,
    MULTIUSER_OT_delete_task,
    MULTIUSER_OT_view_tasks,
    MULTIUSER_PT_tasks,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
