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

import bpy
import mathutils
from bpy.app.handlers import persistent

from . import bl_types, delayable, environment, presence, ui, utils
from .libs.replication.replication.constants import (FETCHED, STATE_ACTIVE,
                                                     STATE_INITIAL,
                                                     STATE_SYNCING)
from .libs.replication.replication.data import ReplicatedDataFactory
from .libs.replication.replication.exception import NonAuthorizedOperationError
from .libs.replication.replication.interface import Session

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

client = None
delayables = []
ui_context = None
stop_modal_executor = False
modal_executor_queue = None
server_process = None

def unregister_delayables():
    global delayables, stop_modal_executor

    for d in delayables:
            try:
                d.unregister()
            except:
                continue
    
    stop_modal_executor = True
    
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
        global client, delayables, ui_context, server_process
        settings = context.window_manager.session
        users = bpy.data.window_managers['WinMan'].online_users

        # TODO: Sync server clients
        users.clear()
        delayables.clear()
        # save config
        settings.save(context)

        bpy_factory = ReplicatedDataFactory()
        supported_bl_types = []
        ui_context = context.copy()

        # init the factory with supported types
        for type in bl_types.types_to_register():
            type_module = getattr(bl_types, type)
            type_impl_name = "Bl{}".format(type.split('_')[1].capitalize())
            type_module_class = getattr(type_module, type_impl_name)

            supported_bl_types.append(type_module_class.bl_id)

            # Retreive local replicated types settings
            type_local_config = settings.supported_datablock[type_impl_name]

            bpy_factory.register_type(
                type_module_class.bl_class,
                type_module_class,
                timer=type_local_config.bl_delay_refresh,
                automatic=type_local_config.auto_push)

            if type_local_config.bl_delay_apply > 0:
                delayables.append(delayable.ApplyTimer(
                    timout=type_local_config.bl_delay_apply,
                    target_type=type_module_class))

        client = Session(
            factory=bpy_factory,
            python_path=bpy.app.binary_path_python,
            default_strategy=settings.right_strategy)

        # Host a session
        if self.host:
            # Scene setup
            if settings.start_empty:
                utils.clean_scene()

            try:
                for scene in bpy.data.scenes:
                    scene_uuid = client.add(scene)
                    client.commit(scene_uuid)

                client.host(
                    id=settings.username,
                    address=settings.ip,
                    port=settings.port,
                    ipc_port=settings.ipc_port)
            except Exception as e:
                self.report({'ERROR'}, repr(e))
                logger.error(f"Error: {e}")
            finally:
                settings.is_admin = True

        # Join a session
        else:
            utils.clean_scene()

            try:
                client.connect(
                    id=settings.username,
                    address=settings.ip,
                    port=settings.port,
                    ipc_port=settings.ipc_port
                )
            except Exception as e:
                self.report({'ERROR'}, repr(e))
                logger.error(f"Error: {e}")
            finally:
                settings.is_admin = False

        # Background client updates service
        #TODO: Refactoring
        delayables.append(delayable.ClientUpdate())
        delayables.append(delayable.DrawClient())
        delayables.append(delayable.DynamicRightSelectTimer())

        # Launch drawing module
        if settings.enable_presence:
            presence.renderer.run()

        # Register blender main thread tools
        for d in delayables:
            d.register()

        global modal_executor_queue
        modal_executor_queue = queue.Queue()
        bpy.ops.session.apply_armature_operator()

        self.report(
            {'INFO'},
            "connexion on tcp://{}:{}".format(settings.ip, settings.port))
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
        assert(client)     

        try:
            client.disconnect()
        except Exception as e:
            self.report({'ERROR'}, repr(e))

        return {"FINISHED"}


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
        settings = context.window_manager.session

        col = layout.column()
        col.prop(settings, "clients")

    def execute(self, context):
        settings = context.window_manager.session
        global client

        if client:
            client.change_owner(self.key, settings.clients)

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
        settings = context.window_manager.session

        if settings.time_snap_running:
            settings.time_snap_running = False
            return {'CANCELLED'}
        else:
            settings.time_snap_running = True

        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

    def modal(self, context, event):
        is_running = context.window_manager.session.time_snap_running

        if event.type in {'RIGHTMOUSE', 'ESC'} or not is_running:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            area, region, rv3d = presence.view3d_find()
            global client

            if client:
                target_ref = client.online_users.get(self.target_client)

                if target_ref:
                    rv3d.view_matrix = mathutils.Matrix(
                        target_ref['metadata']['view_matrix'])
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
        settings = context.window_manager.session

        if settings.user_snap_running:
            settings.user_snap_running = False
            return {'CANCELLED'}
        else:
            settings.user_snap_running = True

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
                            logger.error(
                                "fail to apply {}: {}".format(node_ref.uuid, e))

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

)


@persistent
def load_pre_handler(dummy):
    global client

    if client and client.state['STATE'] in [STATE_ACTIVE, STATE_SYNCING]:
        bpy.ops.session.stop()


@persistent
def sanitize_deps_graph(dummy):
    """sanitize deps graph

    Temporary solution to resolve each node pointers after a Undo.
    A future solution should be to avoid storing dataclock reference...

    """
    global client

    if client and client.state['STATE'] in [STATE_ACTIVE]:
        for node_key in client.list():
            client.get(node_key).resolve()


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
        session_infos = bpy.context.window_manager.session

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
                if node.owner in [session_infos.username, 'COMMON']:
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

    bpy.app.handlers.load_pre.append(load_pre_handler)

    bpy.app.handlers.undo_post.append(sanitize_deps_graph)
    bpy.app.handlers.redo_post.append(sanitize_deps_graph)

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

    bpy.app.handlers.load_pre.remove(load_pre_handler)

    bpy.app.handlers.undo_post.remove(sanitize_deps_graph)
    bpy.app.handlers.redo_post.remove(sanitize_deps_graph)

    bpy.app.handlers.frame_change_pre.remove(update_client_frame)

    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_evaluation)


if __name__ == "__main__":
    register()
