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


class MULTIUSER_OT_scene_create_blank(bpy.types.Operator):
    """Create a new blank scene in the collaborative session"""
    bl_idname = "multiuser.scene_create_blank"
    bl_label = "Create Blank Scene"
    bl_description = "Create a new empty scene that all users can access"
    bl_options = {'REGISTER', 'UNDO'}

    scene_name: bpy.props.StringProperty(
        name="Scene Name",
        description="Name for the new scene",
        default="New Scene"
    )

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "scene_name")

    def execute(self, context):
        if not session or session.state != STATE_ACTIVE:
            self.report({'ERROR'}, "Not connected to a session")
            return {'CANCELLED'}

        # Check if scene name already exists
        if self.scene_name in bpy.data.scenes:
            self.report({'ERROR'}, f"Scene '{self.scene_name}' already exists")
            return {'CANCELLED'}

        try:
            # Create the blank scene
            new_scene = bpy.data.scenes.new(self.scene_name)

            # Add the scene to the repository
            scene_uuid = porcelain.add(session.repository, new_scene)
            porcelain.commit(session.repository, scene_uuid)
            porcelain.push(session.repository, 'origin', scene_uuid)

            # Switch to the new scene
            context.window.scene = new_scene

            self.report({'INFO'}, f"Created blank scene '{self.scene_name}'")
            logging.info(f"Created blank collaborative scene: {self.scene_name}")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to create scene: {str(e)}")
            logging.error(f"Failed to create scene: {e}")
            return {'CANCELLED'}


class MULTIUSER_OT_scene_create_copy(bpy.types.Operator):
    """Create a copy of the current scene"""
    bl_idname = "multiuser.scene_create_copy"
    bl_label = "Duplicate Current Scene"
    bl_description = "Create a copy of the current scene that all users can access"
    bl_options = {'REGISTER', 'UNDO'}

    scene_name: bpy.props.StringProperty(
        name="Scene Name",
        description="Name for the new scene",
        default="Scene Copy"
    )

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def invoke(self, context, event):
        # Default name based on current scene
        self.scene_name = f"{context.scene.name}_Copy"
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "scene_name")

    def execute(self, context):
        if not session or session.state != STATE_ACTIVE:
            self.report({'ERROR'}, "Not connected to a session")
            return {'CANCELLED'}

        # Check if scene name already exists
        if self.scene_name in bpy.data.scenes:
            self.report({'ERROR'}, f"Scene '{self.scene_name}' already exists")
            return {'CANCELLED'}

        try:
            # Copy the current scene
            new_scene = context.scene.copy()
            new_scene.name = self.scene_name

            # Add the scene to the repository
            scene_uuid = porcelain.add(session.repository, new_scene)
            porcelain.commit(session.repository, scene_uuid)
            porcelain.push(session.repository, 'origin', scene_uuid)

            # Switch to the new scene
            context.window.scene = new_scene

            self.report({'INFO'}, f"Created scene copy '{self.scene_name}'")
            logging.info(f"Created scene copy: {self.scene_name}")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to create scene: {str(e)}")
            logging.error(f"Failed to create scene: {e}")
            return {'CANCELLED'}


class MULTIUSER_OT_scene_switch(bpy.types.Operator):
    """Switch to a different scene in the session"""
    bl_idname = "multiuser.scene_switch"
    bl_label = "Switch Scene"
    bl_description = "Switch to this collaborative scene"

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


class MULTIUSER_OT_import_objects_popup(bpy.types.Operator):
    """Show popup to select scene for importing objects"""
    bl_idname = "multiuser.import_objects_popup"
    bl_label = "Import Objects from Scene"
    bl_description = "Import objects from another scene into the current scene"

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE and context.mode == 'OBJECT'

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=400)

    def draw(self, context):
        layout = self.layout

        layout.label(text="Select Scene to Import From:", icon='SCENE_DATA')
        layout.separator()

        scenes = [s for s in bpy.data.scenes if s.name != context.scene.name]
        if not scenes:
            layout.label(text="No other scenes available", icon='INFO')
            layout.label(text="Create a new scene first")
        else:
            box = layout.box()
            for scene in scenes:
                row = box.row()
                row.label(text=scene.name, icon='SCENE_DATA')
                row.label(text=f"({len(scene.objects)} objects)")
                props = row.operator("multiuser.import_objects_from_scene",
                                    text="Select", icon='FORWARD')
                props.source_scene = scene.name

    def execute(self, context):
        return {'FINISHED'}


class MULTIUSER_OT_import_objects_from_scene(bpy.types.Operator):
    """Import objects from selected scene"""
    bl_idname = "multiuser.import_objects_from_scene"
    bl_label = "Import Objects"
    bl_description = "Choose which objects to import from this scene"

    source_scene: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def invoke(self, context, event):
        source = bpy.data.scenes.get(self.source_scene)
        if not source:
            return {'CANCELLED'}

        return context.window_manager.invoke_popup(self, width=500)

    def draw(self, context):
        layout = self.layout
        source = bpy.data.scenes.get(self.source_scene)

        if not source:
            layout.label(text="Scene not found", icon='ERROR')
            return

        layout.label(text=f"Import from: {self.source_scene}", icon='SCENE_DATA')
        layout.separator()

        # Get all objects from source scene
        objects = [obj for obj in source.objects]

        if not objects:
            layout.label(text="No objects in this scene", icon='INFO')
        else:
            # Show "Import All" button prominently
            box = layout.box()
            col = box.column(align=True)
            row = col.row()
            row.scale_y = 1.5
            props = row.operator("multiuser.import_all_objects",
                                text=f"Import All Objects ({len(objects)})",
                                icon='IMPORT')
            props.source_scene = self.source_scene

            layout.separator()
            layout.label(text="Or import individual objects:")

            # List of objects
            box = layout.box()
            col = box.column(align=True)

            for obj in objects[:15]:  # Limit to 15 for UI performance
                row = col.row()
                row.label(text=obj.name, icon='OBJECT_DATA')
                row.label(text=obj.type)
                props = row.operator("multiuser.import_single_object",
                                    text="Import", icon='IMPORT')
                props.source_scene = self.source_scene
                props.object_name = obj.name

            if len(objects) > 15:
                col.separator()
                col.label(text=f"...and {len(objects) - 15} more objects")
                col.label(text="Use 'Import All' to get everything")

    def execute(self, context):
        return {'FINISHED'}


class MULTIUSER_OT_import_single_object(bpy.types.Operator):
    """Import a single object from another scene"""
    bl_idname = "multiuser.import_single_object"
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


class MULTIUSER_OT_import_all_objects(bpy.types.Operator):
    """Import all objects from another scene"""
    bl_idname = "multiuser.import_all_objects"
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


# UI Panel for Scene Management in 3D View
class MULTIUSER_PT_scene_management(bpy.types.Panel):
    """Panel for managing collaborative scenes"""
    bl_label = "Scenes"
    bl_idname = "MULTIUSER_PT_scene_management"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Multi-User'
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return session and session.state == STATE_ACTIVE

    def draw(self, context):
        layout = self.layout

        # Current scene info
        box = layout.box()
        row = box.row()
        row.label(text="Current Scene:", icon='SCENE_DATA')
        row = box.row()
        row.label(text=context.scene.name, icon='DOT')
        row.scale_y = 0.8

        layout.separator()

        # Create scene buttons - prominent
        box = layout.box()
        box.label(text="Create New Scene:", icon='ADD')
        col = box.column(align=True)
        col.scale_y = 1.2
        col.operator("multiuser.scene_create_blank", text="Create Blank Scene", icon='FILE_NEW')
        col.operator("multiuser.scene_create_copy", text="Duplicate Current Scene", icon='DUPLICATE')

        layout.separator()

        # Available scenes list
        scenes = [s for s in bpy.data.scenes]
        if len(scenes) > 1:
            box = layout.box()
            box.label(text="Available Scenes:", icon='OUTLINER_COLLECTION')
            col = box.column(align=True)

            for scene in scenes:
                if scene != context.scene:
                    row = col.row(align=True)
                    row.label(text="", icon='SCENE_DATA')
                    props = row.operator("multiuser.scene_switch",
                                        text=scene.name)
                    props.scene_name = scene.name
                    row.label(text=f"{len(scene.objects)} obj")
        else:
            box = layout.box()
            col = box.column()
            col.label(text="Only one scene exists", icon='INFO')
            col.label(text="Create more scenes to switch between them")

        layout.separator()

        # Import objects button - clear and prominent
        box = layout.box()
        box.label(text="Import Objects:", icon='IMPORT')
        col = box.column(align=True)
        col.scale_y = 1.2

        other_scenes = [s for s in bpy.data.scenes if s.name != context.scene.name]
        if other_scenes:
            col.operator("multiuser.import_objects_popup",
                        text=f"Import from Other Scenes ({len(other_scenes)})",
                        icon='IMPORT')
        else:
            col.enabled = False
            col.operator("multiuser.import_objects_popup",
                        text="No Other Scenes Available",
                        icon='INFO')
            col.label(text="Create a scene first")


classes = (
    MULTIUSER_OT_scene_create_blank,
    MULTIUSER_OT_scene_create_copy,
    MULTIUSER_OT_scene_switch,
    MULTIUSER_OT_import_objects_popup,
    MULTIUSER_OT_import_objects_from_scene,
    MULTIUSER_OT_import_single_object,
    MULTIUSER_OT_import_all_objects,
    MULTIUSER_PT_scene_management,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
