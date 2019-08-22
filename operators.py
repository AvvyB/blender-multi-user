import asyncio
import logging
import os
import queue
import random
import string
import subprocess
import time
from operator import itemgetter
from pathlib import Path

import bpy
import mathutils
from bpy_extras.io_utils import ExportHelper

from . import environment, presence, ui, utils, delayable
from .libs import umsgpack
from .libs.replication.data import ReplicatedDataFactory
from .libs.replication.interface import Client
from . import bl_types

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

client = None
delayables = []
ui_context = None

def add_datablock(datablock):
    global client
    child = []

    if hasattr(datablock, "data"):
        child.append(add_datablock(datablock.data))
    if hasattr(datablock, "materials"):
        for mat in datablock.materials:
            child.append(add_datablock(mat))
    if hasattr(datablock, "collection") and hasattr(datablock.collection, "children"):
        for coll in datablock.collection.children:
            child.append(add_datablock(coll))
    if hasattr(datablock, "children"):
        for coll in datablock.children:
            child.append(add_datablock(coll))
    if hasattr(datablock, "objects"):
        for obj in datablock.objects:
            child.append(add_datablock(obj))
    if hasattr(datablock,'uuid') and datablock.uuid and client.exist(datablock.uuid):
        return datablock.uuid
    else:
        new_uuid = client.add(datablock, childs=child)
        datablock.uuid = new_uuid
        return new_uuid


# TODO: cleanup
def init_supported_datablocks(supported_types_id):
    global client

    for type_id in supported_types_id:
        if hasattr(bpy.data, type_id):
            for item in getattr(bpy.data, type_id):
                add_datablock(item)



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
        global client, delayables
        settings = context.window_manager.session
        # save config
        settings.save(context)

        # Scene setup
        if settings.start_empty:
            utils.clean_scene()

        bpy_factory = ReplicatedDataFactory()
        supported_bl_types = []

        # init the factory with supported types
        for type in bl_types.types_to_register():
            _type = getattr(bl_types, type)
            supported_bl_types.append(_type.bl_id)

            bpy_factory.register_type(_type.bl_class, _type.bl_rep_class, timer=_type.bl_delay_refresh,automatic=True)
            
            if _type.bl_delay_apply > 0:
                delayables.append(delayable.ApplyTimer(timout=_type.bl_delay_apply,target_type=_type.bl_rep_class))
           
        client = Client(factory=bpy_factory)

        if self.host:
            client.host(
                id=settings.username,
                address=settings.ip,
                port=settings.port
            )

            if settings.init_scene:
                init_supported_datablocks(supported_bl_types)
        else:
            client.connect(
                id=settings.username,
                address=settings.ip,
                port=settings.port
            )

        usr = presence.User(
            username=settings.username,
            color=(settings.client_color.r,
                settings.client_color.g,
                settings.client_color.b,
                1),
        )
        
        settings.user_uuid = client.add(usr)
        delayables.append(delayable.ClientUpdate(client_uuid=settings.user_uuid))
        
        # Push all added values 
        client.push()

        # Launch drawing module
        if settings.enable_presence:
            presence.renderer.run()
        
        for d in delayables:
            d.register()

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
        global client, delayables

        assert(client)

        client.disconnect()

        for d in delayables:
            d.unregister()
        
        presence.renderer.stop()

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
        global client

        if client:
            client.right(self.key,settings.clients)
        

        return {"FINISHED"}


class SessionSnapUserOperator(bpy.types.Operator):
    bl_idname = "session.snapview"
    bl_label = "draw client_instances"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER"}

    target_client: bpy.props.StringProperty(default="None")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        area, region, rv3d = presence.view3d_find()
        global client

        target_client = client.get(self.target_client)
        if target_client:
            rv3d.view_location = target_client.buffer['location'][0]
            rv3d.view_distance = 30.0

            return {"FINISHED"}

        return {"CANCELLED"}

        pass


class SessionApply(bpy.types.Operator):
    bl_idname = "session.apply"
    bl_label = "apply the target item into the blender data"
    bl_description = "Apply target object into blender data"
    bl_options = {"REGISTER"}

    target = bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client

        client.apply(uuid=self.target)

        return {"FINISHED"}


classes = (
    SessionStartOperator,
    SessionStopOperator,
    SessionPropertyRemoveOperator,
    SessionSnapUserOperator,
    SessionPropertyRightOperator,
    SessionApply,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    presence.register()


def unregister():
    global client

    presence.unregister()

    if client and client.state == 2:
        client.disconnect()
        client = None

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
