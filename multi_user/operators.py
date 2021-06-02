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
import copy
import gzip
import logging
import os
import queue
import random
import shutil
import string
import sys
import time
from datetime import datetime
from operator import itemgetter
from pathlib import Path
from queue import Queue
from time import gmtime, strftime
import traceback

try:
    import _pickle as pickle
except ImportError:
    import pickle

import bpy
import mathutils
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper, ImportHelper
from replication.constants import (COMMITED, FETCHED, RP_COMMON, STATE_ACTIVE,
                                   STATE_INITIAL, STATE_SYNCING, UP)
from replication.protocol import DataTranslationProtocol
from replication.exception import ContextError, NonAuthorizedOperationError
from replication.interface import session
from replication import porcelain
from replication.repository import Repository
from replication.objects import Node

from . import bl_types, environment, timers, ui, utils
from .presence import SessionStatusWidget, renderer, view3d_find
from .timers import registry

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
    logging.info("Intializing the scene")
    settings = utils.get_preferences()
    runtime_settings = bpy.context.window_manager.session

    # Step 1: Constrect nodes
    logging.info("Constructing nodes")
    for node in session.repository.list_ordered():
        node_ref = session.repository.get_node(node)
        if node_ref is None:
            logging.error(f"Can't construct node {node}")
        elif node_ref.state == FETCHED:
            node_ref.instance = session.repository.rdp.resolve(node_ref.data)
            if node_ref.instance is None:
                node_ref.instance = session.repository.rdp.construct(node_ref.data)
                node_ref.instance.uuid = node_ref.uuid

    # Step 2: Load nodes
    logging.info("Loading nodes")
    for node in session.repository.list_ordered():
        porcelain.apply(session.repository, node)

    logging.info("Registering timers")
    # Step 4: Register blender timers
    for d in deleyables:
        d.register()

    bpy.ops.session.apply_armature_operator('INVOKE_DEFAULT')

    # Step 5: Clearing history
    utils.flush_history()

    # Step 6: Launch deps graph update handling
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_evaluation)


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

    if depsgraph_evaluation in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_evaluation)

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

        users.clear()
        deleyables.clear()

        logger = logging.getLogger()
        if len(logger.handlers) == 1:
            formatter = logging.Formatter(
                fmt='%(asctime)s CLIENT %(levelname)-8s %(message)s',
                datefmt='%H:%M:%S'
            )

            start_time = datetime.now().strftime('%Y_%m_%d_%H-%M-%S')
            log_directory = os.path.join(
                settings.cache_directory,
                f"multiuser_{start_time}.log")

            os.makedirs(settings.cache_directory, exist_ok=True)

            handler = logging.FileHandler(log_directory, mode='w')
            logger.addHandler(handler)

            for handler in logger.handlers:
                if isinstance(handler, logging.NullHandler):
                    continue

                handler.setFormatter(formatter)

        bpy_protocol = bl_types.get_data_translation_protocol()

        # Check if supported_datablocks are up to date before starting the
        # the session
        for dcc_type_id in bpy_protocol.implementations.keys():
            if dcc_type_id not in settings.supported_datablocks:
                logging.info(f"{dcc_type_id} not found, \
                             regenerate type settings...")
                settings.generate_supported_types()


        if bpy.app.version[1] >= 91:
            python_binary_path = sys.executable
        else:
            python_binary_path = bpy.app.binary_path_python

        repo = Repository(
            rdp=bpy_protocol,
            username=settings.username)
    
        # Host a session
        if self.host:
            if settings.init_method == 'EMPTY':
                utils.clean_scene()

            runtime_settings.is_host = True
            runtime_settings.internet_ip = environment.get_ip()

            try:
                # Init repository
                for scene in bpy.data.scenes:
                    porcelain.add(repo, scene)

                porcelain.remote_add(
                    repo,
                    'origin',
                    '127.0.0.1',
                    settings.port,
                    admin_password=admin_pass)
                session.host(
                    repository= repo,
                    remote='origin',
                    timeout=settings.connection_timeout,
                    password=admin_pass,
                    cache_directory=settings.cache_directory,
                    server_log_level=logging.getLevelName(
                        logging.getLogger().level),
                )
            except Exception as e:
                self.report({'ERROR'}, repr(e))
                logging.error(f"Error: {e}")
                traceback.print_exc()
        # Join a session
        else:
            if not runtime_settings.admin:
                utils.clean_scene()
                # regular session, no password needed
                admin_pass = None

            try:
                porcelain.remote_add(
                    repo,
                    'origin',
                    settings.ip,
                    settings.port,
                    admin_password=admin_pass)
                session.connect(
                    repository= repo,
                    timeout=settings.connection_timeout,
                    password=admin_pass
                )
            except Exception as e:
                self.report({'ERROR'}, str(e))
                logging.error(str(e))

        # Background client updates service
        deleyables.append(timers.ClientUpdate())
        deleyables.append(timers.DynamicRightSelectTimer())
        deleyables.append(timers.ApplyTimer(timeout=settings.depsgraph_update_rate))

        session_update = timers.SessionStatusUpdate()
        session_user_sync = timers.SessionUserSync()
        session_background_executor = timers.MainThreadExecutor(
            execution_queue=background_execution_queue)
        session_listen = timers.SessionListenTimer(timeout=0.001)

        session_listen.register()
        session_update.register()
        session_user_sync.register()
        session_background_executor.register()

        deleyables.append(session_background_executor)
        deleyables.append(session_update)
        deleyables.append(session_user_sync)
        deleyables.append(session_listen)
        

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
            porcelain.add(session.repository, scene)

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
                session.disconnect(reason='user')

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
            porcelain.kick(session.repository, self.user)
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
            porcelain.rm(session.repository, self.property_path)

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
            if runtime_settings.clients == RP_COMMON:
                session.unlock(self.key,
                               ignore_warnings=True,
                               affect_dependencies=self.recursive)
            else:
                session.lock(self.key,
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
        if not is_running:
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
            node_ref = session.repository.get_node(self.target)
            porcelain.apply(session.repository,
                            self.target,
                            force=True,
                            force_dependencies=self.reset_dependencies)
            impl = session.repository.rdp.get_implementation(node_ref.instance)
            if impl.bl_reload_parent:
                for parent in session.repository.get_parents(self.target):
                    logging.debug(f"Refresh parent {parent}")

                    porcelain.apply(session.repository,
                                    parent.uuid,
                                    force=True)
        except Exception as e:
            self.report({'ERROR'}, repr(e))
            traceback.print_exc()
            return {"CANCELLED"}    

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
            porcelain.commit(session.repository, self.target)
            porcelain.push(session.repository, 'origin', self.target)
            return {"FINISHED"}
        except Exception as e:
            self.report({'ERROR'}, repr(e))
            return {"CANCELLED"}

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
            if session and session.state == STATE_ACTIVE:
                nodes = session.list(filter=bl_types.bl_armature.BlArmature)

                for node in nodes:
                    node_ref = session.repository.get_node(node)

                    if node_ref.state == FETCHED:
                        try:
                            porcelain.apply(session.repository, node)
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

class SessionPurgeOperator(bpy.types.Operator):
    "Remove node with lost references"
    bl_idname = "session.purge"
    bl_label = "Purge session data"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        try:
            sanitize_deps_graph(remove_nodes=True)
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


class SessionSaveBackupOperator(bpy.types.Operator, ExportHelper):
    bl_idname = "session.save"
    bl_label = "Save session data"
    bl_description = "Save a snapshot of the collaborative session"

    # ExportHelper mixin class uses this
    filename_ext = ".db"

    filter_glob: bpy.props.StringProperty(
        default="*.db",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    enable_autosave: bpy.props.BoolProperty(
        name="Auto-save",
        description="Enable session auto-save",
        default=True,
    )
    save_interval: bpy.props.FloatProperty(
        name="Auto save interval",
        description="auto-save interval (seconds)",
        default=10,
    )

    def execute(self, context):
        if self.enable_autosave:
            recorder = timers.SessionBackupTimer(
                filepath=self.filepath,
                timeout=self.save_interval)
            recorder.register()
            deleyables.append(recorder)
        else:
            session.repository.dumps(self.filepath)

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return session.state == STATE_ACTIVE

class SessionStopAutoSaveOperator(bpy.types.Operator):
    bl_idname = "session.cancel_autosave"
    bl_label = "Cancel auto-save"
    bl_description = "Cancel session auto-save"

    @classmethod
    def poll(cls, context):
        return (session.state == STATE_ACTIVE and 'SessionBackupTimer' in registry)

    def execute(self, context):
        autosave_timer = registry.get('SessionBackupTimer')
        autosave_timer.unregister()

        return {'FINISHED'}


class SessionLoadSaveOperator(bpy.types.Operator, ImportHelper):
    bl_idname = "session.load"
    bl_label = "Load session save"
    bl_description = "Load a Multi-user session save"
    bl_options = {'REGISTER', 'UNDO'}

    # ExportHelper mixin class uses this
    filename_ext = ".db"

    filter_glob: bpy.props.StringProperty(
        default="*.db",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        from replication.repository import Repository

        # init the factory with supported types
        bpy_protocol = bl_types.get_data_translation_protocol()
        repo = Repository(bpy_protocol)
        repo.loads(self.filepath)
        utils.clean_scene()

        nodes = [repo.get_node(n) for n in repo.list_ordered()]

        # Step 1: Construct nodes
        for node in nodes:
            node.instance = bpy_protocol.resolve(node.data)
            if node.instance is None:
                node.instance = bpy_protocol.construct(node.data)
                node.instance.uuid = node.uuid

        # Step 2: Load nodes
        for node in nodes:
            porcelain.apply(repo, node.uuid)


        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return True

def menu_func_import(self, context):
    self.layout.operator(SessionLoadSaveOperator.bl_idname, text='Multi-user session snapshot (.db)')


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
    SessionSaveBackupOperator,
    SessionLoadSaveOperator,
    SessionStopAutoSaveOperator,
    SessionPurgeOperator,
)

def update_external_dependencies():
    nodes_ids = session.list(filter=bl_types.bl_file.BlFile)
    for node_id in nodes_ids:
        node = session.repository.get_node(node_id)
        if node and node.owner in [session.id, RP_COMMON]:
            porcelain.commit(session.repository, node_id)
            porcelain.push(session.repository,'origin', node_id)

def sanitize_deps_graph(remove_nodes: bool = False):
    """ Cleanup the replication graph
    """
    if session and session.state == STATE_ACTIVE:
        start = utils.current_milli_time()
        rm_cpt = 0
        for node_key in session.list():
            node = session.repository.get_node(node_key)
            node.instance = session.repository.rdp.resolve(node.data)
            if node is None \
                    or (node.state == UP and not node.instance):
                if remove_nodes:
                    try:
                        porcelain.rm(session.repository,
                                     node.uuid,
                                     remove_dependencies=False)
                        logging.info(f"Removing {node.uuid}")
                        rm_cpt += 1
                    except NonAuthorizedOperationError:
                        continue
        logging.info(f"Sanitize took { utils.current_milli_time()-start} ms, removed {rm_cpt} nodes")


@persistent
def resolve_deps_graph(dummy):
    """Resolve deps graph

    Temporary solution to resolve each node pointers after a Undo.
    A future solution should be to avoid storing dataclock reference...

    """
    if session and session.state == STATE_ACTIVE:
        sanitize_deps_graph(remove_nodes=True)

@persistent
def load_pre_handler(dummy):
    if session and session.state in [STATE_ACTIVE, STATE_SYNCING]:
        bpy.ops.session.stop()


@persistent
def update_client_frame(scene):
    if session and session.state == STATE_ACTIVE:
        session.update_user_metadata({
            'frame_current': scene.frame_current
        })


@persistent
def depsgraph_evaluation(scene):
    if session and session.state == STATE_ACTIVE:
        context = bpy.context
        blender_depsgraph = bpy.context.view_layer.depsgraph
        dependency_updates = [u for u in blender_depsgraph.updates]
        settings = utils.get_preferences()

        update_external_dependencies()

        # NOTE: maybe we don't need to check each update but only the first
        for update in reversed(dependency_updates):
            # Is the object tracked ?
            if update.id.uuid:
                # Retrieve local version
                node = session.repository.get_node(update.id.uuid)
                check_common = session.repository.rdp.get_implementation(update.id).bl_check_common
                # Check our right on this update:
                #   - if its ours or ( under common and diff), launch the
                # update process
                #   - if its to someone else, ignore the update
                if node and (node.owner == session.id or check_common):
                    if node.state == UP:
                        try:
                            porcelain.commit(session.repository, node.uuid)
                            porcelain.push(session.repository, 'origin', node.uuid)
                        except ReferenceError:
                            logging.debug(f"Reference error {node.uuid}")
                        except ContextError as e:
                            logging.debug(e) 
                        except Exception as e:
                            logging.error(e)
                else:
                    continue
            # A new scene is created 
            elif isinstance(update.id, bpy.types.Scene):
                ref = session.repository.get_node_by_datablock(update.id)
                if ref:
                    pass
                else:
                    scn_uuid = porcelain.add(session.repository, update.id)
                    porcelain.commit(session.node_id, scn_uuid)
                    porcelain.push(session.repository,'origin', scn_uuid)
def register():
    from bpy.utils import register_class

    for cls in classes: 
        register_class(cls)


    bpy.app.handlers.undo_post.append(resolve_deps_graph)
    bpy.app.handlers.redo_post.append(resolve_deps_graph)

    bpy.app.handlers.load_pre.append(load_pre_handler)
    bpy.app.handlers.frame_change_pre.append(update_client_frame)


def unregister():
    if session and session.state == STATE_ACTIVE:
        session.disconnect()

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    bpy.app.handlers.undo_post.remove(resolve_deps_graph)
    bpy.app.handlers.redo_post.remove(resolve_deps_graph)

    bpy.app.handlers.load_pre.remove(load_pre_handler)
    bpy.app.handlers.frame_change_pre.remove(update_client_frame)
