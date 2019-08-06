import asyncio
import logging
import os
import random
import string
import subprocess
import time
import queue
from operator import itemgetter


import bpy
from bpy_extras.io_utils import ExportHelper
import mathutils
from pathlib import Path

from . import environment, presence, ui, utils
from .libs import umsgpack
from .libs.replication.client import Client
from .libs.replication.data import ReplicatedDataFactory

logger = logging.getLogger(__name__)

client = None

context = None
execution_queue = queue.Queue()

# This function can savely be called in another thread.
# The function will be executed when the timer runs the next time.


# def run_in_main_thread(function, args):
#     execution_queue.put(function)


# def execute_queued_functions():
#     while not execution_queue.empty():
#         function, args = execution_queue.get()
#         function(args[0], args[1])
#     return .1


# def clean_scene(elements=environment.rtypes):
#     for datablock in elements:
#         datablock_ref = getattr(bpy.data,  utils.BPY_TYPES[datablock])
#         for item in datablock_ref:
#             try:
#                 datablock_ref.remove(item)
#             # Catch last scene remove
#             except RuntimeError:
#                 pass


# def upload_client_instance_position():
#     username = bpy.context.window_manager.session.username
#     if client:

#         key = "Client/{}".format(username)

#         current_coords = presence.get_client_view_rect()
#         client_list = client.get(key)

#         if current_coords and client_list:
#             if current_coords != client_list[0][1]['location']:
#                 client_list[0][1]['location'] = current_coords
#                 client.set(key, client_list[0][1])


# def update_client_selected_object(context):
    # session = bpy.context.window_manager.session
    # username = bpy.context.window_manager.session.username
    # client_key = "Client/{}".format(username)
    # client_data = client.get(client_key)

    # selected_objects = utils.get_selected_objects(context.scene)
    # if len(selected_objects) > 0 and len(client_data) > 0:

    #     for obj in selected_objects:
    #         # if obj not in client_data[0][1]['active_objects']:
    #         client_data[0][1]['active_objects'] = selected_objects

    #         client.set(client_key, client_data[0][1])
    #         break

    # elif client_data and client_data[0][1]['active_objects']:
    #     client_data[0][1]['active_objects'] = []
    #     client.set(client_key, client_data[0][1])

# TODO: cleanup
# def init_datablocks():
#     for datatype in environment.rtypes:
#         if bpy.context.window_manager.session.supported_datablock[datatype].is_replicated:
#             for item in getattr(bpy.data, utils.BPY_TYPES[datatype]):
#                 item.id = bpy.context.window_manager.session.username
#                 key = "{}/{}".format(datatype, item.name)
#                 client.set(key)


# def default_tick():
#     upload_client_instance_position()

#     return .1


# def register_ticks():
#     # REGISTER Updaters
#     bpy.app.timers.register(default_tick)
#     bpy.app.timers.register(execute_queued_functions)


# def unregister_ticks():
    # REGISTER Updaters
    # try:
    #     bpy.app.timers.unregister(default_tick)
    #     bpy.app.timers.unregister(execute_queued_functions)
    # except:
    #     pass


# OPERATORS
class SessionStartOperator(bpy.types.Operator):
    bl_idname = "session.start"
    bl_label = "start"
    bl_description = "connect to a net server"
    bl_options = {"REGISTER"}

    host: bpy.props.BoolProperty(default=False)


    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global execution_queue, client
        settings = context.window_manager.session
        # save config
        settings.save(context)
        
        # Scene setup
        if settings.start_empty:
            clean_scene()

        # Setup data factory
        bpy_factory = ReplicatedDataFactory()

        # Setup client
        client = Client(factory=bpy_factory)

        if self.host:
            client.host(
            id=settings.username,
            address=settings.ip,
            port=settings.port
            )
        else:
            client.connect(
                id=settings.username,
                address=settings.ip,
                port=settings.port
                )

        # settings.is_running = True
        # bpy.ops.session.refresh()
        #register_ticks()

        # Launch drawing module
        if settings.enable_presence:
            presence.renderer.run()

        return {"FINISHED"}


class SessionStopOperator(bpy.types.Operator):
    bl_idname = "session.stop"
    bl_label = "close"
    bl_description = "stop net service"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client

        assert(client)
        
        client.disconnect()

            # del client_instance


            # unregister_ticks()
            # presence.renderer.stop()

        return {"FINISHED"}


class SessionPropertyAddOperator(bpy.types.Operator):
    bl_idname = "session.add_prop"
    bl_label = "add"
    bl_description = "broadcast a property to connected client_instances"
    bl_options = {"REGISTER"}

    property_path: bpy.props.StringProperty(default="None")
    depth: bpy.props.IntProperty(default=1)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client

        client.add(self.property_path)

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
            del client.property_map[self.property_path]

            return {"FINISHED"}
        except:
            return {"CANCELED"}


class SessionPropertyRightOperator(bpy.types.Operator):
    bl_idname = "session.right"
    bl_label = "Change owner to"
    bl_description = "stop net service"
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

        if settings.is_admin:
            val = client.get(self.key)
            val[0][1]['id'] = settings.clients

            client.set(key=self.key, value=val[0][1], override=True)
            item = utils.resolve_bpy_path(self.key)
            if item:
                item.id = settings.clients
                logger.info("Updating {} rights to {}".format(
                    self.key, settings.clients))
        else:
            print("Not admin")

        return {"FINISHED"}


class SessionSnapUserOperator(bpy.types.Operator):
    bl_idname = "session.snapview"
    bl_label = "draw client_instances"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER"}

    target_client = bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        area, region, rv3d = presence.view3d_find()

        target_client = client.get(
            "Client/{}".format(self.target_client))
        if target_client:
            rv3d.view_location = target_client[0][1]['location'][0]
            rv3d.view_distance = 30.0

            return {"FINISHED"}

        return {"CANCELLED"}

        pass


class SessionDumpDatabase(bpy.types.Operator, ExportHelper):
    bl_idname = "session.dump"
    bl_label = "dump json data"
    bl_description = "dump session stored data to a json file"
    bl_options = {"REGISTER"}

    # ExportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        print(self.filepath)
        if client and client.state() == 3:
            client.dump(self.filepath)
            return {"FINISHED"}

        return {"CANCELLED"}

        pass


class SessionSaveConfig(bpy.types.Operator):
    bl_idname = "session.save"
    bl_label = "Save session configuration"
    bl_description = "Save session configuration"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        context.window_manager.session.save()


classes = (
    SessionStartOperator,
    SessionPropertyAddOperator,
    SessionStopOperator,
    SessionPropertyRemoveOperator,
    SessionSnapUserOperator,
    SessionPropertyRightOperator,
    SessionDumpDatabase,
    SessionSaveConfig,
)

"""
def get_datablock_from_update(update,context):
    item_type = update.id.__class__.__name__
    item_id = update.id.name
   
    datablock_ref = None

    if item_id == 'Master Collection':
        datablock_ref= bpy.context.scene
    elif item_type in utils.BPY_TYPES.keys():
        datablock_ref = getattr(bpy.data, utils.BPY_TYPES[update.id.__class__.__name__])[update.id.name]
    else:
        if item_id in bpy.data.lights.keys():
            datablock_ref = bpy.data.lights[item_id]
    

    return datablock_ref


def depsgraph_update(scene):
    ctx = bpy.context

    if client and client.state() == 3:
        if ctx.mode in ['OBJECT','PAINT_GPENCIL']:
            updates = ctx.view_layer.depsgraph.updates
            username = ctx.window_manager.session.username
            

            selected_objects = utils.get_selected_objects(scene)

            for update in reversed(updates):
                if is_replicated(update):
                    if update.id.id == username or update.id.id == 'Common':
                        toogle_update_dirty(ctx, update)
                else:
                    item = get_datablock_from_update(update,ctx)
                    
                    # get parent authority
                    if hasattr(item,"id"):
                        parent_id = ctx.collection.id if ctx.collection.id != 'None' else ctx.scene.id 

                        if parent_id == username or parent_id == 'Common':
                            item.id = username

                            item_type = item.__class__.__name__
                            
                            if 'Light'in item.__class__.__name__:
                                item_type = 'Light'
                                
                            key = "{}/{}".format(item_type , item.name)
                            client.set(key)
                        else:
                            try:
                                getattr(bpy.data, utils.BPY_TYPES[update.id.__class__.__name__]).remove(item)
                            except:
                                pass
                            break

            update_client_selected_object(ctx)   

"""

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
   
    # bpy.app.handlers.depsgraph_update_post.append(depsgraph_update)
    presence.register()


def unregister():
    global client

    presence.unregister()

    # if  bpy.app.handlers.depsgraph_update_post.count(depsgraph_update) > 0:
    #     bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update)

    if client:
        client.disconnect()
        client = None

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
