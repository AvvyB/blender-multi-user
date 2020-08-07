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


import asyncio
import logging
import os
import queue
import random
import string
import time
from operator import itemgetter
from pathlib import Path
from subprocess import PIPE, Popen, TimeoutExpired
import zmq

import bpy
import mathutils
from bpy.app.handlers import persistent

from . import bl_types, delayable, environment, presence, ui, utils
from replication.constants import (FETCHED, STATE_ACTIVE,
                                                     STATE_INITIAL,
                                                     STATE_SYNCING, RP_COMMON, UP)
from replication.data import ReplicatedDataFactory
from replication.exception import NonAuthorizedOperationError
from replication.interface import Session


client = None
delayables = []
stop_modal_executor = False


# OPERATORS


class SessionStartOperator(bpy.types.Operator):
    bl_idname = "session.start"
    bl_label = "start"
    bl_description = "connect to a net server"

    host: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client, delayables

        settings = utils.get_preferences()
        runtime_settings = context.window_manager.session
        users = bpy.data.window_managers['WinMan'].online_users
        admin_pass = runtime_settings.password

        users.clear()
        delayables.clear()

        bpy_factory = ReplicatedDataFactory()
        supported_bl_types = []

        # init the factory with supported types
        for type in bl_types.types_to_register():
            type_module = getattr(bl_types, type)
            type_impl_name = f"Bl{type.split('_')[1].capitalize()}"
            type_module_class = getattr(type_module, type_impl_name)

            supported_bl_types.append(type_module_class.bl_id)

            # Retreive local replicated types settings
            type_local_config = settings.supported_datablocks[type_impl_name]

            bpy_factory.register_type(
                type_module_class.bl_class,
                type_module_class,
                timer=type_local_config.bl_delay_refresh,
                automatic=type_local_config.auto_push)

        client = Session(
            factory=bpy_factory,
            python_path=bpy.app.binary_path_python)

        delayables.append(delayable.ApplyTimer())

        # Host a session
        if self.host:
            if settings.init_method == 'EMPTY':
                utils.clean_scene()

            runtime_settings.is_host = True
            runtime_settings.internet_ip = environment.get_ip()

            for scene in bpy.data.scenes:
                client.add(scene)

            try:
                client.host(
                    id=settings.username,
                    port=settings.port,
                    ipc_port=settings.ipc_port,
                    timeout=settings.connection_timeout,
                    password=admin_pass
                )
            except Exception as e:
                self.report({'ERROR'}, repr(e))
                logging.error(f"Error: {e}")

        # Join a session
        else:
            if not runtime_settings.admin:
                utils.clean_scene()
                # regular client, no password needed
                admin_pass = None

            try:
                client.connect(
                    id=settings.username,
                    address=settings.ip,
                    port=settings.port,
                    ipc_port=settings.ipc_port,
                    timeout=settings.connection_timeout,
                    password=admin_pass
                )
            except Exception as e:
                self.report({'ERROR'}, str(e))
                logging.error(str(e))

        # Background client updates service
        #TODO: Refactoring
        delayables.append(delayable.ClientUpdate())
        delayables.append(delayable.DrawClient())
        delayables.append(delayable.DynamicRightSelectTimer())

        session_update = delayable.SessionStatusUpdate()
        session_user_sync = delayable.SessionUserSync()
        session_update.register()
        session_user_sync.register()

        delayables.append(session_update)
        delayables.append(session_user_sync)


        @client.register('on_connection')
        def initialize_session():
            for node in client._graph.list_ordered():
                node_ref = client.get(node)
                if node_ref.state == FETCHED:
                    node_ref.resolve()
                    node_ref.apply()

            # Launch drawing module
            if runtime_settings.enable_presence:
                presence.renderer.run()

            # Register blender main thread tools
            for d in delayables:
                d.register()

        @client.register('on_exit')
        def desinitialize_session():
            global delayables, stop_modal_executor

            for d in delayables:
                try:
                    d.unregister()
                except:
                    continue

            stop_modal_executor = True
            presence.renderer.stop()

        bpy.ops.session.apply_armature_operator()

        self.report(
            {'INFO'},
            f"connecting to tcp://{settings.ip}:{settings.port}")
        return {"FINISHED"}


class SessionInitOperator(bpy.types.Operator):
    bl_idname = "session.init"
    bl_label = "Init session repostitory from"
    bl_description = "Init the current session"
    bl_options = {"REGISTER"}

    init_method: bpy.props.EnumProperty(
        name='init_method',
        description='Init repo',
        items={
            ('EMPTY', 'an empty scene', 'start empty'),
            ('BLEND', 'current scenes', 'use current scenes')},
        default='BLEND')

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, 'init_method', text="")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        global client

        if self.init_method == 'EMPTY':
            utils.clean_scene()

        for scene in bpy.data.scenes:
            client.add(scene)

        client.init()

        return {"FINISHED"}


class SessionStopOperator(bpy.types.Operator):
    bl_idname = "session.stop"
    bl_label = "close"
    bl_description = "Exit current session"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client, delayables, stop_modal_executor

        if client:
            try:
                client.disconnect()
            except Exception as e:
                self.report({'ERROR'}, repr(e))
        else:
            self.report({'WARNING'}, "No session to quit.")
            return {"FINISHED"}
        return {"FINISHED"}


class SessionKickOperator(bpy.types.Operator):
    bl_idname = "session.kick"
    bl_label = "Kick"
    bl_description = "Kick the user"
    bl_options = {"REGISTER"}

    user: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client, delayables, stop_modal_executor
        assert(client)

        try:
            client.kick(self.user)
        except Exception as e:
            self.report({'ERROR'}, repr(e))

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout
        row.label(text=f" Do you really want to kick {self.user} ? ")


class SessionPropertyRemoveOperator(bpy.types.Operator):
    bl_idname = "session.remove_prop"
    bl_label = "remove"
    bl_description = "broadcast a property to connected client_instances"
    bl_options = {"REGISTER"}

    property_path: bpy.props.StringProperty(default="None")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client
        try:
            client.remove(self.property_path)

            return {"FINISHED"}
        except:  # NonAuthorizedOperationError:
            self.report(
                {'ERROR'},
                "Non authorized operation")
            return {"CANCELLED"}


class SessionPropertyRightOperator(bpy.types.Operator):
    bl_idname = "session.right"
    bl_label = "Change owner to"
    bl_description = "Change owner of specified datablock"
    bl_options = {"REGISTER"}

    key: bpy.props.StringProperty(default="None")

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        runtime_settings = context.window_manager.session

        col = layout.column()
        col.prop(runtime_settings, "clients")

    def execute(self, context):
        runtime_settings = context.window_manager.session
        global client

        if client:
            client.change_owner(self.key, runtime_settings.clients)

        return {"FINISHED"}


class SessionSnapUserOperator(bpy.types.Operator):
    bl_idname = "session.snapview"
    bl_label = "snap to user"
    bl_description = "Snap 3d view to selected user"
    bl_options = {"REGISTER"}

    _timer = None

    target_client: bpy.props.StringProperty(default="None")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        wm = context.window_manager
        runtime_settings = context.window_manager.session

        if runtime_settings.time_snap_running:
            runtime_settings.time_snap_running = False
            return {'CANCELLED'}
        else:
            runtime_settings.time_snap_running = True

        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

    def modal(self, context, event):
        session_sessings = context.window_manager.session
        is_running = session_sessings.time_snap_running

        if event.type in {'RIGHTMOUSE', 'ESC'} or not is_running:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            area, region, rv3d = presence.view3d_find()
            global client

            if client:
                target_ref = client.online_users.get(self.target_client)

                if target_ref:
                    target_scene = target_ref['metadata']['scene_current']

                    # Handle client on other scenes
                    if target_scene != context.scene.name:
                        blender_scene = bpy.data.scenes.get(target_scene, None)
                        if blender_scene is None:
                            self.report({'ERROR'}, f"Scene {target_scene} doesn't exist on the local client.")
                            session_sessings.time_snap_running = False
                            return {"CANCELLED"}

                        bpy.context.window.scene = blender_scene

                    # Update client viewmatrix
                    client_vmatrix = target_ref['metadata'].get('view_matrix', None)

                    if client_vmatrix:
                        rv3d.view_matrix = mathutils.Matrix(client_vmatrix)
                    else:
                        self.report({'ERROR'}, f"Client viewport not ready.")
                        session_sessings.time_snap_running = False
                        return {"CANCELLED"}
            else:
                return {"CANCELLED"}

        return {'PASS_THROUGH'}


class SessionSnapTimeOperator(bpy.types.Operator):
    bl_idname = "session.snaptime"
    bl_label = "snap to user time"
    bl_description = "Snap time to selected user time's"
    bl_options = {"REGISTER"}

    _timer = None

    target_client: bpy.props.StringProperty(default="None")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        runtime_settings = context.window_manager.session

        if runtime_settings.user_snap_running:
            runtime_settings.user_snap_running = False
            return {'CANCELLED'}
        else:
            runtime_settings.user_snap_running = True

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

    def modal(self, context, event):
        is_running = context.window_manager.session.user_snap_running
        if event.type in {'RIGHTMOUSE', 'ESC'} or not is_running:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            global client

            if client:
                target_ref = client.online_users.get(self.target_client)

                if target_ref:
                    context.scene.frame_current = target_ref['metadata']['frame_current']
            else:
                return {"CANCELLED"}

        return {'PASS_THROUGH'}


class SessionApply(bpy.types.Operator):
    bl_idname = "session.apply"
    bl_label = "apply selected block into blender"
    bl_description = "Apply selected block into blender"
    bl_options = {"REGISTER"}

    target: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client

        client.apply(self.target)

        return {"FINISHED"}


class SessionCommit(bpy.types.Operator):
    bl_idname = "session.commit"
    bl_label = "commit and push selected datablock to server"
    bl_description = "commit and push selected datablock to server"
    bl_options = {"REGISTER"}

    target: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client
        # client.get(uuid=target).diff()
        client.commit(uuid=self.target)
        client.push(self.target)
        return {"FINISHED"}


class ApplyArmatureOperator(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "session.apply_armature_operator"
    bl_label = "Modal Executor Operator"

    _timer = None

    def modal(self, context, event):
        global stop_modal_executor, modal_executor_queue
        if stop_modal_executor:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            global client
            if client and client.state['STATE'] == STATE_ACTIVE:
                nodes = client.list(filter=bl_types.bl_armature.BlArmature)

                for node in nodes:
                    node_ref = client.get(uuid=node)

                    if node_ref.state == FETCHED:
                        try:
                            client.apply(node)
                        except Exception as e:
                            logging.error("Fail to apply armature: {e}")

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(2, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        global stop_modal_executor

        wm = context.window_manager
        wm.event_timer_remove(self._timer)

        stop_modal_executor = False


classes = (
    SessionStartOperator,
    SessionStopOperator,
    SessionPropertyRemoveOperator,
    SessionSnapUserOperator,
    SessionSnapTimeOperator,
    SessionPropertyRightOperator,
    SessionApply,
    SessionCommit,
    ApplyArmatureOperator,
    SessionKickOperator,
    SessionInitOperator,

)


@persistent
def sanitize_deps_graph(dummy):
    """sanitize deps graph

    Temporary solution to resolve each node pointers after a Undo.
    A future solution should be to avoid storing dataclock reference...

    """
    global client

    if client and client.state['STATE'] == STATE_ACTIVE:
        for node_key in client.list():
            client.get(node_key).resolve()


@persistent
def load_pre_handler(dummy):
    global client

    if client and client.state['STATE'] in [STATE_ACTIVE, STATE_SYNCING]:
        bpy.ops.session.stop()


@persistent
def update_client_frame(scene):
    if client and client.state['STATE'] == STATE_ACTIVE:
        client.update_user_metadata({
            'frame_current': scene.frame_current
        })

@persistent
def depsgraph_evaluation(scene):
    if client and client.state['STATE'] == STATE_ACTIVE:
        context = bpy.context
        blender_depsgraph = bpy.context.view_layer.depsgraph
        dependency_updates = [u for u in blender_depsgraph.updates]
        session_infos = utils.get_preferences()

        # NOTE: maybe we don't need to check each update but only the first

        for update in reversed(dependency_updates):
            # Is the object tracked ?
            if update.id.uuid:
                # Retrieve local version
                node = client.get(update.id.uuid)
                
                # Check our right on this update:
                #   - if its ours or ( under common and diff), launch the
                # update process
                #   - if its to someone else, ignore the update (go deeper ?)
                if node.owner in [client.id, RP_COMMON] and node.state == UP:
                    # Avoid slow geometry update
                    if 'EDIT' in context.mode:
                        break

                    client.stash(node.uuid)
                else:
                    # Distant update
                    continue
            # else:
            #     # New items !
            #     logger.error("UPDATE: ADD")


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.app.handlers.undo_post.append(sanitize_deps_graph)
    bpy.app.handlers.redo_post.append(sanitize_deps_graph)

    bpy.app.handlers.load_pre.append(load_pre_handler)
    bpy.app.handlers.frame_change_pre.append(update_client_frame)

    bpy.app.handlers.depsgraph_update_post.append(depsgraph_evaluation)


def unregister():
    global client

    if client and client.state['STATE'] == 2:
        client.disconnect()
        client = None

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    bpy.app.handlers.undo_post.remove(sanitize_deps_graph)
    bpy.app.handlers.redo_post.remove(sanitize_deps_graph)

    bpy.app.handlers.load_pre.remove(load_pre_handler)
    bpy.app.handlers.frame_change_pre.remove(update_client_frame)
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_evaluation)