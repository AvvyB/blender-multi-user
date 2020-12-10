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
import shutil
import string
import sys
import time
from operator import itemgetter
from pathlib import Path
from queue import Queue

import bpy
import mathutils
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper

from replication.constants import (FETCHED, RP_COMMON, STATE_ACTIVE,
                                   STATE_INITIAL, STATE_SYNCING, UP)
from replication.data import ReplicatedDataFactory
from replication.exception import NonAuthorizedOperationError
from replication.interface import session

from . import bl_types, delayable, environment, ui, utils
from .presence import SessionStatusWidget, renderer, view3d_find

background_execution_queue = Queue()
deleyables = []
stop_modal_executor = False


def session_callback(name):
    """ Session callback wrapper

    This allow to encapsulate session callbacks to background_execution_queue.
    By doing this way callback are executed from the main thread. 
    """
    def func_wrapper(func):
        @session.register(name)
        def add_background_task(**kwargs):
            background_execution_queue.put((func, kwargs))
        return add_background_task
    return func_wrapper


@session_callback('on_connection')
def initialize_session():
    """Session connection init hander 
    """
    settings = utils.get_preferences()
    runtime_settings = bpy.context.window_manager.session

    # Step 1: Constrect nodes
    for node in session._graph.list_ordered():
        node_ref = session.get(node)
        if node_ref.state == FETCHED:
            node_ref.resolve()

    # Step 2: Load nodes
    for node in session._graph.list_ordered():
        node_ref = session.get(node)
        if node_ref.state == FETCHED:
            node_ref.apply()

    # Step 4: Register blender timers
    for d in deleyables:
        d.register()

    if settings.update_method == 'DEPSGRAPH':
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_evaluation)

    bpy.ops.session.apply_armature_operator('INVOKE_DEFAULT')


@session_callback('on_exit')
def on_connection_end(reason="none"):
    """Session connection finished handler 
    """
    global deleyables, stop_modal_executor
    settings = utils.get_preferences()

    # Step 1: Unregister blender timers
    for d in deleyables:
        try:
            d.unregister()
        except:
            continue
    deleyables.clear()

    stop_modal_executor = True

    if settings.update_method == 'DEPSGRAPH':
        bpy.app.handlers.depsgraph_update_post.remove(
            depsgraph_evaluation)

    # Step 3: remove file handled
    logger = logging.getLogger()
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)
    if reason != "user":
        bpy.ops.session.notify('INVOKE_DEFAULT', message=f"Disconnected from session. Reason: {reason}. ")


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
        global deleyables

        settings = utils.get_preferences()
        runtime_settings = context.window_manager.session
        users = bpy.data.window_managers['WinMan'].online_users
        admin_pass = runtime_settings.password
        use_extern_update = settings.update_method == 'DEPSGRAPH'
        users.clear()
        deleyables.clear()

        logger = logging.getLogger()
        if len(logger.handlers) == 1:
            formatter = logging.Formatter(
                fmt='%(asctime)s CLIENT %(levelname)-8s %(message)s',
                datefmt='%H:%M:%S'
            )

            log_directory = os.path.join(
                settings.cache_directory,
                "multiuser_client.log")

            os.makedirs(settings.cache_directory, exist_ok=True)

            handler = logging.FileHandler(log_directory, mode='w')
            logger.addHandler(handler)

            for handler in logger.handlers:
                if isinstance(handler, logging.NullHandler):
                    continue

                handler.setFormatter(formatter)

        bpy_factory = ReplicatedDataFactory()
        supported_bl_types = []

        # init the factory with supported types
        for type in bl_types.types_to_register():
            type_module = getattr(bl_types, type)
            name = [e.capitalize() for e in type.split('_')[1:]]
            type_impl_name = 'Bl'+''.join(name)
            type_module_class = getattr(type_module, type_impl_name)

            supported_bl_types.append(type_module_class.bl_id)

            if type_impl_name not in settings.supported_datablocks:
                logging.info(f"{type_impl_name} not found, \
                             regenerate type settings...")
                settings.generate_supported_types()

            type_local_config = settings.supported_datablocks[type_impl_name]

            bpy_factory.register_type(
                type_module_class.bl_class,
                type_module_class,
                timer=type_local_config.bl_delay_refresh*1000,
                automatic=type_local_config.auto_push,
                check_common=type_module_class.bl_check_common)

            if settings.update_method == 'DEFAULT':
                if type_local_config.bl_delay_apply > 0:
                    deleyables.append(
                        delayable.ApplyTimer(
                            timout=type_local_config.bl_delay_apply,
                            target_type=type_module_class))

        if bpy.app.version[1] >= 91:
            python_binary_path = sys.executable
        else:
            python_binary_path = bpy.app.binary_path_python

        session.configure(
            factory=bpy_factory,
            python_path=python_binary_path,
            external_update_handling=use_extern_update)

        if settings.update_method == 'DEPSGRAPH':
            deleyables.append(delayable.ApplyTimer(
                settings.depsgraph_update_rate/1000))

        # Host a session
        if self.host:
            if settings.init_method == 'EMPTY':
                utils.clean_scene()

            runtime_settings.is_host = True
            runtime_settings.internet_ip = environment.get_ip()

            try:
                for scene in bpy.data.scenes:
                    session.add(scene)

                session.host(
                    id=settings.username,
                    port=settings.port,
                    ipc_port=settings.ipc_port,
                    timeout=settings.connection_timeout,
                    password=admin_pass,
                    cache_directory=settings.cache_directory,
                    server_log_level=logging.getLevelName(
                        logging.getLogger().level),
                )
            except Exception as e:
                self.report({'ERROR'}, repr(e))
                logging.error(f"Error: {e}")
                import traceback
                traceback.print_exc()
        # Join a session
        else:
            if not runtime_settings.admin:
                utils.clean_scene()
                # regular session, no password needed
                admin_pass = None

            try:
                session.connect(
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
        deleyables.append(delayable.ClientUpdate())
        deleyables.append(delayable.DynamicRightSelectTimer())

        session_update = delayable.SessionStatusUpdate()
        session_user_sync = delayable.SessionUserSync()
        session_background_executor = delayable.MainThreadExecutor(
            execution_queue=background_execution_queue)

        session_update.register()
        session_user_sync.register()
        session_background_executor.register()

        deleyables.append(session_background_executor)
        deleyables.append(session_update)
        deleyables.append(session_user_sync)

        

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
        if self.init_method == 'EMPTY':
            utils.clean_scene()

        for scene in bpy.data.scenes:
            session.add(scene)

        session.init()

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
        global deleyables, stop_modal_executor

        if session:
            try:
                session.disconnect()

            except Exception as e:
                self.report({'ERROR'}, repr(e))
        else:
            self.report({'WARNING'}, "No session to quit.")
            return {"FINISHED"}
        return {"FINISHED"}


class SessionKickOperator(bpy.types.Operator):
    bl_idname = "session.kick"
    bl_label = "Kick"
    bl_description = "Kick the target user"
    bl_options = {"REGISTER"}

    user: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global deleyables, stop_modal_executor
        assert(session)

        try:
            session.kick(self.user)
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
    bl_label = "Delete cache"
    bl_description = "Stop tracking modification on the target datablock." + \
        "The datablock will no longer be updated for others client. "
    bl_options = {"REGISTER"}

    property_path: bpy.props.StringProperty(default="None")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        try:
            session.remove(self.property_path)

            return {"FINISHED"}
        except:  # NonAuthorizedOperationError:
            self.report(
                {'ERROR'},
                "Non authorized operation")
            return {"CANCELLED"}


class SessionPropertyRightOperator(bpy.types.Operator):
    bl_idname = "session.right"
    bl_label = "Change modification rights"
    bl_description = "Modify the owner of the target datablock"
    bl_options = {"REGISTER"}

    key: bpy.props.StringProperty(default="None")
    recursive: bpy.props.BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        runtime_settings = context.window_manager.session

        row = layout.row()
        row.label(text="Give the owning rights to:")
        row.prop(runtime_settings, "clients", text="")
        row = layout.row()
        row.label(text="Affect dependencies")
        row.prop(self, "recursive", text="")

    def execute(self, context):
        runtime_settings = context.window_manager.session

        if session:
            session.change_owner(self.key,
                                 runtime_settings.clients,
                                 ignore_warnings=True,
                                 affect_dependencies=self.recursive)

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
            area, region, rv3d = view3d_find()

            if session:
                target_ref = session.online_users.get(self.target_client)

                if target_ref:
                    target_scene = target_ref['metadata']['scene_current']

                    # Handle client on other scenes
                    if target_scene != context.scene.name:
                        blender_scene = bpy.data.scenes.get(target_scene, None)
                        if blender_scene is None:
                            self.report(
                                {'ERROR'}, f"Scene {target_scene} doesn't exist on the local client.")
                            session_sessings.time_snap_running = False
                            return {"CANCELLED"}

                        bpy.context.window.scene = blender_scene

                    # Update client viewmatrix
                    client_vmatrix = target_ref['metadata'].get(
                        'view_matrix', None)

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
            if session:
                target_ref = session.online_users.get(self.target_client)

                if target_ref:
                    context.scene.frame_current = target_ref['metadata']['frame_current']
            else:
                return {"CANCELLED"}

        return {'PASS_THROUGH'}


class SessionApply(bpy.types.Operator):
    bl_idname = "session.apply"
    bl_label = "Revert"
    bl_description = "Revert the selected datablock from his cached" + \
        " version."
    bl_options = {"REGISTER"}

    target: bpy.props.StringProperty()
    reset_dependencies: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        logging.debug(f"Running apply on {self.target}")
        try:
            session.apply(self.target,
                        force=True,
                        force_dependencies=self.reset_dependencies)
        except Exception as e:
            self.report({'ERROR'}, repr(e))
            return {"CANCELED"}    

        return {"FINISHED"}


class SessionCommit(bpy.types.Operator):
    bl_idname = "session.commit"
    bl_label = "Force server update"
    bl_description = "Commit and push the target datablock to server"
    bl_options = {"REGISTER"}

    target: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        try:
            session.commit(uuid=self.target)
            session.push(self.target)
            return {"FINISHED"}
        except Exception as e:
            self.report({'ERROR'}, repr(e))
            return {"CANCELED"}

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
            if session and session.state['STATE'] == STATE_ACTIVE:
                nodes = session.list(filter=bl_types.bl_armature.BlArmature)

                for node in nodes:
                    node_ref = session.get(uuid=node)

                    if node_ref.state == FETCHED:
                        try:
                            session.apply(node)
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


class SessionClearCache(bpy.types.Operator):
    "Clear local session cache"
    bl_idname = "session.clear_cache"
    bl_label = "Modal Executor Operator"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        cache_dir = utils.get_preferences().cache_directory
        try:
            for root, dirs, files in os.walk(cache_dir):
                for name in files:
                    Path(root, name).unlink()

        except Exception as e:
            self.report({'ERROR'}, repr(e))

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout
        row.label(text=f" Do you really want to remove local cache ? ")

class SessionNotifyOperator(bpy.types.Operator):
    """Dialog only operator"""
    bl_idname = "session.notify"
    bl_label = "Multi-user"
    bl_description = "multiuser notification"

    message: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.row().label(text=self.message)


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class SessionRecordGraphOperator(bpy.types.Operator, ExportHelper):
    bl_idname = "session.export"
    bl_label = "SessionRecordGraph"

    # ExportHelper mixin class uses this
    filename_ext = ".db"

    @classmethod
    def poll(cls, context):
        return session.state['STATE'] == STATE_ACTIVE

    def execute(self, context):
        import networkx as nx
        import pickle
        import copy

        # Replication graph 
        nodes_ids = session.list()
        #TODO: add dump graph to replication

        nodes =[]
        for n in nodes_ids:
            nd = session.get(uuid=n)
            nodes.append((
                n,
                {
                    'owner': nd.owner,
                    'str_type': nd.str_type,
                    'data': nd.data,
                    'dependencies': nd.dependencies,
                }
            ))

        G = nx.DiGraph()
        G.add_nodes_from(nodes)

        for n, nd in nodes:
            relations = [(n,d) for d in nd['dependencies']]
            G.add_edges_from(relations)

        
        # Users
        G.graph['users'] = copy.copy(session.online_users)

        with open(self.filepath, "wb") as f:
            pickle.dump(G, f, protocol=4)

        return {'FINISHED'}


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
    SessionClearCache,
    SessionNotifyOperator,
    SessionRecordGraphOperator,
)


@persistent
def sanitize_deps_graph(dummy):
    """sanitize deps graph

    Temporary solution to resolve each node pointers after a Undo.
    A future solution should be to avoid storing dataclock reference...

    """
    if session and session.state['STATE'] == STATE_ACTIVE:
        for node_key in session.list():
            session.get(node_key).resolve()


@persistent
def load_pre_handler(dummy):
    if session and session.state['STATE'] in [STATE_ACTIVE, STATE_SYNCING]:
        bpy.ops.session.stop()


@persistent
def update_client_frame(scene):
    if session and session.state['STATE'] == STATE_ACTIVE:
        session.update_user_metadata({
            'frame_current': scene.frame_current
        })


@persistent
def depsgraph_evaluation(scene):
    if session and session.state['STATE'] == STATE_ACTIVE:
        context = bpy.context
        blender_depsgraph = bpy.context.view_layer.depsgraph
        dependency_updates = [u for u in blender_depsgraph.updates]
        settings = utils.get_preferences()

        # NOTE: maybe we don't need to check each update but only the first

        for update in reversed(dependency_updates):
            # Is the object tracked ?
            if update.id.uuid:
                # Retrieve local version
                node = session.get(update.id.uuid)

                # Check our right on this update:
                #   - if its ours or ( under common and diff), launch the
                # update process
                #   - if its to someone else, ignore the update (go deeper ?)
                if node and node.owner in [session.id, RP_COMMON] and node.state == UP:
                    # Avoid slow geometry update
                    if 'EDIT' in context.mode and \
                            not settings.sync_flags.sync_during_editmode:
                        break

                    session.stash(node.uuid)
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


def unregister():
    if session and session.state['STATE'] == STATE_ACTIVE:
        session.disconnect()

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    bpy.app.handlers.undo_post.remove(sanitize_deps_graph)
    bpy.app.handlers.redo_post.remove(sanitize_deps_graph)

    bpy.app.handlers.load_pre.remove(load_pre_handler)
    bpy.app.handlers.frame_change_pre.remove(update_client_frame)
