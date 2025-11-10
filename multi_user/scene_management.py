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
from replication import porcelain
from replication.constants import STATE_ACTIVE
from replication.interface import session


class MULTIUSER_OT_scene_create(bpy.types.Operator):
    """Create a new scene in the collaborative session"""
    bl_idname = "multiuser.scene_create"
    bl_label = "Create Scene"
    bl_description = "Create a new scene that all users can access"
    bl_options = {'REGISTER', 'UNDO'}

    scene_name: bpy.props.StringProperty(
        name="Scene Name",
        description="Name for the new scene",
        default="Scene"
    )

    init_type: bpy.props.EnumProperty(
        name="Initialize From",
        description="How to initialize the new scene",
        items=[
            ('EMPTY', "Empty", "Create an empty scene"),
            ('COPY', "Copy Current", "Copy the current scene"),
        ],
        default='EMPTY',
    )

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "scene_name")
        layout.prop(self, "init_type")

    def execute(self, context):
        if not session or session.state != STATE_ACTIVE:
            self.report({'ERROR'}, "Not connected to a session")
            return {'CANCELLED'}

        # Check if scene name already exists
        if self.scene_name in bpy.data.scenes:
            self.report({'ERROR'}, f"Scene '{self.scene_name}' already exists")
            return {'CANCELLED'}

        try:
            # Create the scene
            if self.init_type == 'EMPTY':
                new_scene = bpy.data.scenes.new(self.scene_name)
            else:  # COPY
                new_scene = context.scene.copy()
                new_scene.name = self.scene_name

            # Add the scene to the repository
            scene_uuid = porcelain.add(session.repository, new_scene)
            porcelain.commit(session.repository, scene_uuid)
            porcelain.push(session.repository, 'origin', scene_uuid)

            self.report({'INFO'}, f"Created scene '{self.scene_name}'")
            logging.info(f"Created collaborative scene: {self.scene_name}")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to create scene: {str(e)}")
            logging.error(f"Failed to create scene: {e}")
            return {'CANCELLED'}


class MULTIUSER_OT_scene_switch(bpy.types.Operator):
    """Switch to a different scene in the session"""
    bl_idname = "multiuser.scene_switch"
    bl_label = "Switch Scene"
    bl_description = "Switch to a different collaborative scene"

    scene_name: bpy.props.StringProperty(
        name="Scene",
        description="Scene to switch to"
    )

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def execute(self, context):
        if not session or session.state != STATE_ACTIVE:
            self.report({'ERROR'}, "Not connected to a session")
            return {'CANCELLED'}

        # Check if scene exists
        target_scene = bpy.data.scenes.get(self.scene_name)
        if not target_scene:
            self.report({'ERROR'}, f"Scene '{self.scene_name}' not found")
            return {'CANCELLED'}

        # Switch to the scene
        context.window.scene = target_scene

        self.report({'INFO'}, f"Switched to scene '{self.scene_name}'")
        logging.info(f"Switched to scene: {self.scene_name}")

        return {'FINISHED'}


class MULTIUSER_OT_object_import_from_scene(bpy.types.Operator):
    """Import objects from another scene"""
    bl_idname = "multiuser.object_import_from_scene"
    bl_label = "Import Objects"
    bl_description = "Import selected objects from another scene into the current scene"
    bl_options = {'REGISTER', 'UNDO'}

    source_scene: bpy.props.StringProperty(
        name="Source Scene",
        description="Scene to import objects from"
    )

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE and context.mode == 'OBJECT'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout

        # Show available scenes
        layout.label(text="Select Scene to Import From:")

        scenes = [s for s in bpy.data.scenes if s.name != context.scene.name]
        if not scenes:
            layout.label(text="No other scenes available", icon='INFO')
        else:
            for scene in scenes:
                row = layout.row()
                props = row.operator("multiuser.object_import_from_scene_execute",
                                    text=scene.name, icon='SCENE_DATA')
                props.source_scene = scene.name

    def execute(self, context):
        # This is just a UI operator, actual import happens in execute operator
        return {'FINISHED'}


class MULTIUSER_OT_object_import_from_scene_execute(bpy.types.Operator):
    """Execute object import from selected scene"""
    bl_idname = "multiuser.object_import_from_scene_execute"
    bl_label = "Import"
    bl_description = "Import objects from this scene"
    bl_options = {'REGISTER', 'UNDO'}

    source_scene: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def invoke(self, context, event):
        source = bpy.data.scenes.get(self.source_scene)
        if not source:
            return {'CANCELLED'}

        # Show object selection dialog
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        source = bpy.data.scenes.get(self.source_scene)

        if not source:
            layout.label(text="Scene not found", icon='ERROR')
            return

        layout.label(text=f"Objects in '{self.source_scene}':")

        # Get all objects from source scene
        objects = [obj for obj in source.objects]

        if not objects:
            layout.label(text="No objects in this scene", icon='INFO')
        else:
            box = layout.box()
            col = box.column(align=True)

            for obj in objects[:20]:  # Limit to 20 for UI performance
                row = col.row()
                row.label(text=obj.name, icon='OBJECT_DATA')
                props = row.operator("multiuser.object_import_single",
                                    text="Import", icon='IMPORT')
                props.source_scene = self.source_scene
                props.object_name = obj.name

            if len(objects) > 20:
                col.label(text=f"...and {len(objects) - 20} more objects")

            layout.separator()
            row = layout.row()
            row.scale_y = 1.5
            props = row.operator("multiuser.object_import_all",
                                text=f"Import All ({len(objects)} objects)",
                                icon='IMPORT')
            props.source_scene = self.source_scene

    def execute(self, context):
        return {'FINISHED'}


class MULTIUSER_OT_object_import_single(bpy.types.Operator):
    """Import a single object from another scene"""
    bl_idname = "multiuser.object_import_single"
    bl_label = "Import Object"
    bl_description = "Import this object into the current scene"
    bl_options = {'REGISTER', 'UNDO'}

    source_scene: bpy.props.StringProperty()
    object_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def execute(self, context):
        source = bpy.data.scenes.get(self.source_scene)
        if not source:
            self.report({'ERROR'}, f"Scene '{self.source_scene}' not found")
            return {'CANCELLED'}

        source_obj = source.objects.get(self.object_name)
        if not source_obj:
            self.report({'ERROR'}, f"Object '{self.object_name}' not found")
            return {'CANCELLED'}

        try:
            # Link object to current scene if not already present
            if source_obj.name not in context.scene.objects:
                context.scene.collection.objects.link(source_obj)
                self.report({'INFO'}, f"Imported '{self.object_name}'")
                logging.info(f"Imported object '{self.object_name}' from scene '{self.source_scene}'")
            else:
                self.report({'INFO'}, f"'{self.object_name}' already in scene")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to import object: {str(e)}")
            logging.error(f"Failed to import object: {e}")
            return {'CANCELLED'}


class MULTIUSER_OT_object_import_all(bpy.types.Operator):
    """Import all objects from another scene"""
    bl_idname = "multiuser.object_import_all"
    bl_label = "Import All Objects"
    bl_description = "Import all objects from the selected scene"
    bl_options = {'REGISTER', 'UNDO'}

    source_scene: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def execute(self, context):
        source = bpy.data.scenes.get(self.source_scene)
        if not source:
            self.report({'ERROR'}, f"Scene '{self.source_scene}' not found")
            return {'CANCELLED'}

        try:
            imported_count = 0
            skipped_count = 0

            for obj in source.objects:
                if obj.name not in context.scene.objects:
                    context.scene.collection.objects.link(obj)
                    imported_count += 1
                else:
                    skipped_count += 1

            if imported_count > 0:
                self.report({'INFO'},
                           f"Imported {imported_count} objects from '{self.source_scene}' "
                           f"({skipped_count} already present)")
                logging.info(f"Imported {imported_count} objects from scene '{self.source_scene}'")
            else:
                self.report({'INFO'}, "All objects already in scene")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to import objects: {str(e)}")
            logging.error(f"Failed to import objects: {e}")
            return {'CANCELLED'}


# UI Panel for Scene Management
class MULTIUSER_PT_scene_management(bpy.types.Panel):
    """Panel for managing collaborative scenes"""
    bl_label = "Multi-User Scenes"
    bl_idname = "MULTIUSER_PT_scene_management"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Multi-User'

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def draw(self, context):
        layout = self.layout

        # Current scene info
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Current Scene:", icon='SCENE_DATA')
        row = col.row()
        row.label(text=context.scene.name, icon='DOT')

        layout.separator()

        # Create new scene
        box = layout.box()
        box.label(text="Scene Management:", icon='ADD')
        col = box.column(align=True)
        col.operator("multiuser.scene_create", icon='ADD')

        # Available scenes
        scenes = [s for s in bpy.data.scenes]
        if len(scenes) > 1:
            col.separator()
            col.label(text="Switch to Scene:")
            for scene in scenes:
                if scene != context.scene:
                    row = col.row()
                    props = row.operator("multiuser.scene_switch",
                                        text=scene.name, icon='SCENE_DATA')
                    props.scene_name = scene.name

        layout.separator()

        # Import objects
        box = layout.box()
        box.label(text="Import Objects:", icon='IMPORT')
        col = box.column(align=True)

        other_scenes = [s for s in bpy.data.scenes if s.name != context.scene.name]
        if other_scenes:
            col.operator("multiuser.object_import_from_scene", icon='IMPORT')
        else:
            col.label(text="No other scenes available", icon='INFO')


classes = (
    MULTIUSER_OT_scene_create,
    MULTIUSER_OT_scene_switch,
    MULTIUSER_OT_object_import_from_scene,
    MULTIUSER_OT_object_import_from_scene_execute,
    MULTIUSER_OT_object_import_single,
    MULTIUSER_OT_object_import_all,
    MULTIUSER_PT_scene_management,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
