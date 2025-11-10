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
import webbrowser
from datetime import datetime
from collections import deque
from replication.interface import session
from replication.constants import STATE_ACTIVE
from replication import porcelain


class ChatMessage:
    def __init__(self, username, message, msg_type="text", metadata=None):
        self.id = str(time.time())
        self.username = username
        self.message = message
        self.msg_type = msg_type  # text, link, code, image
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.datetime_str = datetime.fromtimestamp(self.timestamp).strftime('%H:%M:%S')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'message': self.message,
            'msg_type': self.msg_type,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }

    @staticmethod
    def from_dict(data):
        msg = ChatMessage(
            username=data['username'],
            message=data['message'],
            msg_type=data.get('msg_type', 'text'),
            metadata=data.get('metadata', {})
        )
        msg.id = data['id']
        msg.timestamp = data['timestamp']
        msg.datetime_str = datetime.fromtimestamp(msg.timestamp).strftime('%H:%M:%S')
        return msg


class ChatManager:
    def __init__(self, max_messages=500):
        self.messages = deque(maxlen=max_messages)
        self.unread_count = 0

    def add_message(self, message):
        self.messages.append(message)
        self.unread_count += 1
        self.sync_messages()

    def get_messages(self, limit=50):
        return list(self.messages)[-limit:]

    def mark_read(self):
        self.unread_count = 0

    def sync_messages(self):
        """Sync messages to server"""
        if session and session.state == STATE_ACTIVE:
            # Send latest messages via metadata
            recent_msgs = [m.to_dict() for m in list(self.messages)[-10:]]  # Last 10 messages
            try:
                porcelain.update_user_metadata(session.repository, {
                    'chat_messages': json.dumps(recent_msgs)
                })
            except Exception as e:
                print(f"Failed to sync chat: {e}")

    def load_messages_from_metadata(self):
        """Load messages from all users"""
        if session and session.state == STATE_ACTIVE:
            for username, user_data in session.online_users.items():
                metadata = user_data.get('metadata', {})
                chat_json = metadata.get('chat_messages')
                if chat_json:
                    try:
                        messages_data = json.loads(chat_json)
                        for msg_dict in messages_data:
                            # Check if we already have this message
                            if not any(m.id == msg_dict['id'] for m in self.messages):
                                msg = ChatMessage.from_dict(msg_dict)
                                self.messages.append(msg)
                                if msg.username != username:  # New message from other user
                                    self.unread_count += 1
                    except:
                        pass

    def clear(self):
        self.messages.clear()
        self.unread_count = 0


# Global instance
chat_manager = ChatManager()


# Operators
class MULTIUSER_OT_send_chat_message(bpy.types.Operator):
    """Send a chat message"""
    bl_idname = "multiuser.send_chat_message"
    bl_label = "Send"
    bl_description = "Send a message to all users"

    message: bpy.props.StringProperty(
        name="Message",
        description="Your message",
        default=""
    )

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def execute(self, context):
        if not self.message.strip():
            return {'CANCELLED'}

        from . import utils
        settings = utils.get_preferences()

        # Detect message type
        msg_type = "text"
        metadata = {}

        if self.message.startswith("http://") or self.message.startswith("https://"):
            msg_type = "link"
        elif self.message.startswith("```") and self.message.endswith("```"):
            msg_type = "code"
            # Extract code content
            code_content = self.message[3:-3].strip()
            metadata['code'] = code_content

        msg = ChatMessage(
            username=settings.username,
            message=self.message,
            msg_type=msg_type,
            metadata=metadata
        )

        chat_manager.add_message(msg)

        # Clear message field
        self.message = ""

        return {'FINISHED'}


class MULTIUSER_OT_open_chat_link(bpy.types.Operator):
    """Open a link from chat"""
    bl_idname = "multiuser.open_chat_link"
    bl_label = "Open Link"
    bl_description = "Open this link in your browser"

    url: bpy.props.StringProperty()

    def execute(self, context):
        webbrowser.open(self.url)
        return {'FINISHED'}


class MULTIUSER_OT_copy_chat_code(bpy.types.Operator):
    """Copy code snippet to clipboard"""
    bl_idname = "multiuser.copy_chat_code"
    bl_label = "Copy Code"
    bl_description = "Copy this code snippet to clipboard"

    code: bpy.props.StringProperty()

    def execute(self, context):
        context.window_manager.clipboard = self.code
        self.report({'INFO'}, "Code copied to clipboard")
        return {'FINISHED'}


class MULTIUSER_OT_view_chat(bpy.types.Operator):
    """View chat messages"""
    bl_idname = "multiuser.view_chat"
    bl_label = "Chat"
    bl_description = "View and send chat messages"

    message_input: bpy.props.StringProperty(
        name="",
        description="Type your message here",
        default=""
    )

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def invoke(self, context, event):
        # Load latest messages
        chat_manager.load_messages_from_metadata()
        chat_manager.mark_read()
        return context.window_manager.invoke_popup(self, width=600)

    def draw(self, context):
        layout = self.layout

        layout.label(text="Team Chat", icon='COMMUNITY')
        layout.separator()

        # Messages area
        box = layout.box()
        col = box.column(align=False)

        messages = chat_manager.get_messages(limit=20)

        if not messages:
            col.label(text="No messages yet. Start chatting!", icon='INFO')
        else:
            for msg in messages:
                # Message header
                row = col.row()
                row.label(text=f"[{msg.datetime_str}]")
                row.label(text=msg.username, icon='USER')

                # Message content based on type
                if msg.msg_type == "link":
                    row = col.row()
                    op = row.operator("multiuser.open_chat_link", text=msg.message, icon='URL')
                    op.url = msg.message
                elif msg.msg_type == "code":
                    code_content = msg.metadata.get('code', msg.message)
                    code_box = col.box()
                    code_col = code_box.column()
                    # Show code lines
                    for line in code_content.split('\n')[:5]:  # Max 5 lines preview
                        code_col.label(text=line)
                    op = code_box.operator("multiuser.copy_chat_code", text="Copy Code", icon='COPYDOWN')
                    op.code = code_content
                else:
                    # Regular text message
                    msg_row = col.row()
                    msg_row.label(text=msg.message)

                col.separator()

        layout.separator()

        # Message input
        box = layout.box()
        col = box.column()
        col.label(text="Send Message:", icon='GREASEPENCIL')
        row = col.row(align=True)
        row.prop(self, "message_input")
        op = row.operator("multiuser.send_chat_message", text="Send", icon='PLAY')
        op.message = self.message_input

        # Help text
        col.separator()
        col.scale_y = 0.7
        col.label(text="Tips: Paste links directly, wrap code in ``` for syntax highlighting", icon='INFO')

    def execute(self, context):
        # Refresh messages
        chat_manager.load_messages_from_metadata()
        return {'FINISHED'}


# UI Panel
class MULTIUSER_PT_chat(bpy.types.Panel):
    """Panel for chat system"""
    bl_label = "Chat"
    bl_idname = "MULTIUSER_PT_chat"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Multi-User'
    bl_order = 4

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)

        # Show unread count
        if chat_manager.unread_count > 0:
            col.label(text=f"{chat_manager.unread_count} New Messages", icon='INFO')

        col.scale_y = 1.3
        col.operator("multiuser.view_chat", text="Open Chat", icon='COMMUNITY')

        layout.separator()

        # Quick message input
        box = layout.box()
        box.label(text="Quick Message:", icon='GREASEPENCIL')
        col = box.column(align=True)

        # Store message in scene property for persistence
        if not hasattr(context.scene, 'multiuser_quick_message'):
            bpy.types.Scene.multiuser_quick_message = bpy.props.StringProperty(
                name="Message",
                default=""
            )

        col.prop(context.scene, "multiuser_quick_message", text="")

        row = col.row(align=True)
        row.scale_y = 1.1

        op = row.operator("multiuser.send_chat_message", text="Send", icon='PLAY')
        if hasattr(context.scene, 'multiuser_quick_message'):
            op.message = context.scene.multiuser_quick_message
            # Clear after sending would require callback

        # Refresh button
        layout.separator()
        col = layout.column()
        col.scale_y = 0.8
        col.operator("multiuser.view_chat", text="Refresh Messages", icon='FILE_REFRESH')


classes = (
    MULTIUSER_OT_send_chat_message,
    MULTIUSER_OT_open_chat_link,
    MULTIUSER_OT_copy_chat_code,
    MULTIUSER_OT_view_chat,
    MULTIUSER_PT_chat,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register scene property for quick message
    if not hasattr(bpy.types.Scene, 'multiuser_quick_message'):
        bpy.types.Scene.multiuser_quick_message = bpy.props.StringProperty(
            name="Message",
            default=""
        )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Unregister scene property
    if hasattr(bpy.types.Scene, 'multiuser_quick_message'):
        del bpy.types.Scene.multiuser_quick_message
