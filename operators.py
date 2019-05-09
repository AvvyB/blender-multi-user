import asyncio
import logging
import os
import queue
import random
import string
import subprocess
import time
from operator import itemgetter
import queue

import bgl
import blf
import bpy
import gpu
import mathutils
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from pathlib import Path

python_path = Path(bpy.app.binary_path_python)
cwd_for_subprocesses = python_path.parent

from . import client, draw, helpers, ui
from .libs import umsgpack

logger = logging.getLogger(__name__)

client_instance = None
client_keys = None
client_state = 1
server = None
context = None
update_list = {}
history = queue.Queue()

# UTILITY FUNCTIONS
def client_list_callback(scene, context):
    global client_keys

    items = [("Common", "Common", "")]

    username = bpy.context.scene.session_settings.username 

    if client_keys:
        for k in client_keys:
            if 'Client' in k[0]:
                name = k[1]
                
                if name == username:
                    name += " (self)"

                items.append((name, name, ""))

    return items


def clean_scene(elements=helpers.SUPPORTED_TYPES):
    for datablock in elements:
        datablock_ref =getattr(bpy.data, helpers.CORRESPONDANCE[datablock])
        for item in datablock_ref:
            try:
                datablock_ref.remove(item)
            #Catch last scene remove
            except RuntimeError:
                pass


def randomStringDigits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


def randomColor():
    r = random.random()
    v = random.random()
    b = random.random()
    return [r, v, b]


def refresh_window():
    import bpy
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)


def upload_client_instance_position():
    global client_instance

    username = bpy.context.scene.session_settings.username
    if client_instance:

        key = "Client/{}".format(username)

        try:
            current_coords = draw.get_client_view_rect()
            client = client_instance.get(key)

            if current_coords != client[0][1]['location']:
                client[0][1]['location'] = current_coords
                client_instance.set(key, client[0][1])
        except:
            pass


def update_selected_object(context):
    global client_instance
    session = bpy.context.scene.session_settings

    username = bpy.context.scene.session_settings.username
    client_key = "Client/{}".format(username)
    client_data = client_instance.get(client_key)

    selected_objects = helpers.get_selected_objects(context.scene)

    if len(selected_objects) > 0:

        for obj in selected_objects:
            # if obj not in client_data[0][1]['active_objects']:
            client_data[0][1]['active_objects'] = selected_objects

            client_instance.set(client_key, client_data[0][1])
            break

    elif client_data and client_data[0][1]['active_objects']:
        client_data[0][1]['active_objects'] = []
        client_instance.set(client_key, client_data[0][1])


def init_datablocks():
    global client_instance

   
    for datatype in helpers.SUPPORTED_TYPES:
        for item in getattr(bpy.data, helpers.CORRESPONDANCE[datatype]):
            item.id = bpy.context.scene.session_settings.username
            key = "{}/{}".format(datatype, item.name)
            client_instance.set(key)
            print(key)
           


def refresh_session_data():
    global client_instance, client_keys, client_state

    keys = client_instance.list()

    if keys:
        client_keys = keys
    state = client_instance.state()

    if state:
        client_state = state


def default_tick():
    refresh_session_data()

    upload_client_instance_position()
    
    global history
    try:
        c = history.get_nowait()
        if c:
            bpy.ops.ed.undo()
    except Exception as e:
        pass

    return .2


def register_ticks():
    # REGISTER Updaters
    bpy.app.timers.register(default_tick)
    


def unregister_ticks():
    # REGISTER Updaters
    bpy.app.timers.unregister(default_tick)
    

# OPERATORS


class session_join(bpy.types.Operator):

    bl_idname = "session.join"
    bl_label = "join"
    bl_description = "connect to a net server"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client_instance

        net_settings = context.scene.session_settings
        # Scene setup
        if net_settings.session_mode == "CONNECT" and net_settings.clear_scene:
            clean_scene()

        # Session setup
        if net_settings.username == "DefaultUser":
            net_settings.username = "{}_{}".format(
                net_settings.username, randomStringDigits())

        username = str(context.scene.session_settings.username)

        if len(net_settings.ip) < 1:
            net_settings.ip = "127.0.0.1"

        client_instance = client.RCFClient()
        client_instance.connect(net_settings.username,
                                net_settings.ip, net_settings.port)

        # net_settings.is_running = True
        # bpy.ops.session.refresh()
        register_ticks()

        # Launch drawing module
        if net_settings.enable_draw:
            draw.renderer.run()

        return {"FINISHED"}


class session_refresh(bpy.types.Operator):
    bl_idname = "session.refresh"
    bl_label = "refresh"
    bl_description = "refresh client ui keys "
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        refresh_session_data()

        return {"FINISHED"}


class session_add_property(bpy.types.Operator):
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
        global client_instance

        client_instance.add(self.property_path)

        return {"FINISHED"}


class session_get_property(bpy.types.Operator):
    bl_idname = "session.get_prop"
    bl_label = "get"
    bl_description = "broadcast a property to connected client_instances"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client_instance

        client_instance.get("client")

        return {"FINISHED"}


class session_remove_property(bpy.types.Operator):
    bl_idname = "session.remove_prop"
    bl_label = "remove"
    bl_description = "broadcast a property to connected client_instances"
    bl_options = {"REGISTER"}

    property_path: bpy.props.StringProperty(default="None")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client_instance

        try:
            del client_instance.property_map[self.property_path]

            return {"FINISHED"}
        except:
            return {"CANCELED"}


class session_create(bpy.types.Operator):
    bl_idname = "session.create"
    bl_label = "create"
    bl_description = "create to a net session"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global server
        global client_instance

        net_settings = context.scene.session_settings

        script = os.path.join(os.path.dirname(os.path.abspath(__file__)),"server.py")

        server = subprocess.Popen(
            [str(python_path),script],shell=False, stdout=subprocess.PIPE)
        # time.sleep(0.1)

        bpy.ops.session.join()

        if net_settings.init_scene:
            init_datablocks()

        # client_instance.init()
        net_settings.is_admin = True

        return {"FINISHED"}


class session_stop(bpy.types.Operator):
    bl_idname = "session.stop"
    bl_label = "close"
    bl_description = "stop net service"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global server
        global client_instance, client_keys, client_state

        net_settings = context.scene.session_settings

        if server:
            server.kill()
            time.sleep(0.25)
            server = None
        if client_instance:
            client_instance.exit()
            time.sleep(0.25)
            del client_instance
            client_instance = None
            client_keys = None
            net_settings.is_admin = False
            client_state = 1
            unregister_ticks()

            # Stop drawing
            draw.renderer.stop()
        else:
            logger.debug("No server/client_instance running.")

        return {"FINISHED"}


class session_rights(bpy.types.Operator):
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
        net_settings = context.scene.session_settings

        col = layout.column()
        col.prop(net_settings, "clients")

    def execute(self, context):
        global server
        global client_instance, client_keys, client_state

        net_settings = context.scene.session_settings

        if net_settings.is_admin:
            val = client_instance.get(self.key)
            val[0][1]['id'] = net_settings.clients

            client_instance.set(key=self.key, value=val[0][1], override=True)

            print("Updating {} rights to {}".format(
                self.key, net_settings.clients))
        else:
            print("Not admin")

        return {"FINISHED"}


class session_settings(bpy.types.PropertyGroup):
    username = bpy.props.StringProperty(
        name="Username", default="user_{}".format(randomStringDigits()))
    ip = bpy.props.StringProperty(
        name="ip", description='Distant host ip', default="127.0.0.1")
    port = bpy.props.IntProperty(
        name="port", description='Distant host port', default=5555)

    add_property_depth = bpy.props.IntProperty(
        name="add_property_depth", default=1)
    buffer = bpy.props.StringProperty(name="None")
    is_admin = bpy.props.BoolProperty(name="is_admin", default=False)
    load_data = bpy.props.BoolProperty(name="load_data", default=True)
    init_scene = bpy.props.BoolProperty(name="load_data", default=True)
    clear_scene = bpy.props.BoolProperty(name="clear_scene", default=True)
    update_frequency = bpy.props.FloatProperty(
        name="update_frequency", default=0.008)
    active_object = bpy.props.PointerProperty(
        name="active_object", type=bpy.types.Object)
    session_mode = bpy.props.EnumProperty(
        name='session_mode',
        description='session mode',
        items={
            ('HOST', 'hosting', 'host a session'),
            ('CONNECT', 'connexion', 'connect to a session')},
        default='HOST')
    client_color = bpy.props.FloatVectorProperty(name="client_instance_color",
                                                 subtype='COLOR',
                                                 default=randomColor())
    clients = bpy.props.EnumProperty(
        name="clients",
        description="client enum",
        items=client_list_callback
    )
    enable_draw = bpy.props.BoolProperty(
        name="enable_draw",  description='Enable overlay drawing module', default=True)


class session_snapview(bpy.types.Operator):
    bl_idname = "session.snapview"
    bl_label = "draw client_instances"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER"}

    target_client = bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client_instance

        area, region, rv3d = draw.view3d_find()

        client = client_instance.get("Client/{}".format(self.target_client))
        if client:
            rv3d.view_location = client[0][1]['location'][0]
            rv3d.view_distance = 30.0

            return {"FINISHED"}

        return {"CANCELLED"}

        pass


# TODO: Rename to match official blender convention
classes = (
    session_join,
    session_refresh,
    session_add_property,
    session_get_property,
    session_stop,
    session_create,
    session_settings,
    session_remove_property,
    session_snapview,
    session_rights,
)


def ordered(updates):
    # sorted = sorted(updates, key=lambda tup: hepers.SUPPORTED_TYPES.index(tup[1].id.bl_rna.name))
    uplist = []
    for item in updates.items():
        if item[1].id.bl_rna.name in hepers.SUPPORTED_TYPES:
            uplist.append((hepers.SUPPORTED_TYPES.index(
                item[1].id.bl_rna.name), item[1].id.bl_rna.name, item[1].id.name, item[1].id))

    uplist.sort(key=itemgetter(0))
    return uplist


def exist(update):
    global client_keys

    key = "{}/{}".format(update.id.bl_rna.name, update.id.name)

    if key in client_keys:
        return True
    else:
        return False

def get_datablock(update,context):
    
    item_type = update.id.__class__.__name__
    item_id = update.id.name
   
    datablock_ref = None

    if item_id == 'Master Collection':
        Adatablock_ref= bpy.context.scene
    elif item_type in helpers.CORRESPONDANCE.keys():
        datablock_ref = getattr(bpy.data, helpers.CORRESPONDANCE[update.id.__class__.__name__])[update.id.name]
    else:
        if item_id in bpy.data.lights.keys():
            datablock_ref = bpy.data.lights[item_id]
    

    return datablock_ref


def depsgraph_update(scene):
    global client_instance
    global client_keys
    global client_state
    

    if client_state == 3:
        if bpy.context.mode == 'OBJECT':
            updates = bpy.context.depsgraph.updates
            username = bpy.context.scene.session_settings.username
            update_selected_object(bpy.context)

            selected_objects = helpers.get_selected_objects(scene)
          
            for update in reversed(updates):
                if update.id.id == username or update.id.id == 'Common' or update.id.id == 'None':
                    # TODO: handle errors
                    data_ref = get_datablock(update,context)
                    
                    if data_ref:
                        data_ref.is_dirty= True
                elif update.id.id != username:
                    history.put("undo")
                        

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.ID.id = bpy.props.StringProperty(default="None")
    bpy.types.ID.is_dirty = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.session_settings = bpy.props.PointerProperty(
        type=session_settings)
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update)
    draw.register()


def unregister():
    global server
    global client_instance, client_keys

    draw.unregister()

    try:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update)
    except:
        pass

    if server:
        server.kill()
        server = None
        del server

    if client_instance:
        client_instance.exit()
        client_instance = None
        del client_instance
        del client_keys

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.session_settings
    del bpy.types.ID.id
    del bpy.types.ID.is_dirty


if __name__ == "__main__":
    register()
