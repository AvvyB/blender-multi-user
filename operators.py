import logging
import random
import string
import time
import asyncio
import queue
from operator import itemgetter
import subprocess
import uuid
import bgl
import blf
import bpy
import os
import gpu
import mathutils
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader

from . import client, ui, draw, helpers


logger = logging.getLogger(__name__)

client_instance = None
client_keys = None
server = None
context = None
drawer = None
update_list = {}
push_tasks = queue.Queue()
pull_tasks = queue.Queue()

def add_update(type, item):
    try:
        if item not in update_list[type]:
            update_list[type].append(item)
    except KeyError:
        update_list[type] = []


def get_update(type):
    try:
        update = None

        if update_list[type]:
            update = update_list[type].pop()
    except KeyError:
        update_list[type] = []

    return update


SUPPORTED_DATABLOCKS = ['collections', 'meshes', 'objects',
                        'materials', 'textures', 'lights', 'cameras', 'actions', 'armatures', 'grease_pencils']
SUPPORTED_TYPES = [ 'Material',
                   'Texture', 'Light', 'Camera','Mesh', 'Grease Pencil', 'Object', 'Action', 'Armature','Collection', 'Scene']

# UTILITY FUNCTIONS


def clean_scene(elements=SUPPORTED_DATABLOCKS):
    for datablock in elements:
        datablock_ref = getattr(bpy.data, datablock)
        for item in datablock_ref:
            datablock_ref.remove(item)


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

    if client_instance:
        key = "net/client_instances/{}".format(client_instance.id.decode())

        try:
            current_coords = net_draw.get_client_instance_view_rect()
            data = client_instance.property_map[key].body
            if data is None:
                data = {}
                data['location'] = current_coords
                color = bpy.context.scene.session_settings.client_instance_color
                data['color'] = (color.r, color.g, color.b, 1)
                client_instance.push_update(key, 'client_instance', data)
            elif current_coords[0] != data['location'][0]:
                data['location'] = current_coords
                client_instance.push_update(key, 'client_instance', data)
        except:
            pass

def update_selected_object(context):
    global client_instance 
    session = bpy.context.scene.session_settings

    # Active object bounding box
    if len(context.selected_objects) > 0:
        if session.active_object is not context.selected_objects[0] or session.active_object.is_evaluated:
            session.active_object = context.selected_objects[0]
            key = "net/objects/{}".format(client_instance.id.decode())
            data = {}
            data['color'] = [session.client_instance_color.r,
                            session.client_instance_color.g, session.client_instance_color.b]
            data['object'] = session.active_object.name
            client_instance.push_update(
                key, 'client_instanceObject', data)
            
            return True
    elif len(context.selected_objects) == 0 and session.active_object:
        session.active_object = None
        data = {}
        data['color'] = [session.client_instance_color.r,
                        session.client_instance_color.g, session.client_instance_color.b]
        data['object'] = None
        key = "net/objects/{}".format(client_instance.id.decode())
        client_instance.push_update(key, 'client_instanceObject', data)

        return True
    
    return False


def init_datablocks():
    global client_instance

    for datatype in SUPPORTED_TYPES:
        for item in getattr(bpy.data,helpers.CORRESPONDANCE[datatype]):
            key = "{}/{}".format(datatype,item.name)
            print(key)
            client_instance.set(key)

def update_scene(msg):
    global client_instance

    
    net_vars = bpy.context.scene.session_settings
    pull_tasks.put(msg.key)
        # if net_vars.active_object:
        #     if net_vars.active_object.name in msg.key:
        #         raise ValueError()

    # if 'net' not in msg.key:
    #     target = resolve_bpy_path(msg.key)
        
    #     if target:
    #         target.is_updating = True

    #     if msg.mtype == 'Object':
    #         load_object(target=target, data=msg.body,
    #                     create=net_vars.load_data)
    #         global drawer
    #         drawer.draw()
    #     elif msg.mtype == 'Mesh':
    #         load_mesh(target=target, data=msg.body,
    #                     create=net_vars.load_data)
    #     elif msg.mtype == 'Collection':
    #         load_collection(target=target, data=msg.body,
    #                         create=net_vars.load_data)
    #     elif msg.mtype == 'Material':
    #         load_material(target=target, data=msg.body,
    #                         create=net_vars.load_data)
    #     elif msg.mtype == 'Grease Pencil':
    #         load_gpencil(target=target, data=msg.body,
    #                         create=net_vars.load_data)
    #     elif msg.mtype == 'Scene':
    #         load_scene(target=target, data=msg.body,
    #                     create=net_vars.load_data)
    #     elif 'Light' in msg.mtype:
    #         load_light(target=target, data=msg.body,
    #                     create=net_vars.load_data)
    #     else:
    #         load_default(target=target, data=msg.body,
    #                         create=net_vars.load_data, type=msg.mtype)
    # else:
    #     if msg.mtype == 'client_instance':
    #         refresh_window()
    #     elif msg.mtype == 'client_instanceObject':
    #         selected_objects = []

    #         for k, v in client_instance.property_map.items():
    #             if v.mtype == 'client_instanceObject':
    #                 if client_instance.id != v.id:
    #                     selected_objects.append(v.body['object'])

    #         for obj in bpy.data.objects:
    #             if obj.name in selected_objects:
    #                 obj.hide_select = True
    #             else:
    #                 obj.hide_select = False

    #         refresh_window()

def push(data_type,id):  
    if data_type == 'Material':
        upload_material(bpy.data.materials[id])
    if data_type == 'Grease Pencil':
        upload_gpencil(bpy.data.grease_pencils[id])
    if data_type == 'Camera':
        dump_datablock(bpy.data.cameras[id], 1)
    if data_type == 'Light':
        dump_datablock(bpy.data.lights[id], 1)
    if data_type == 'Mesh':
        upload_mesh(bpy.data.meshes[id])
    if data_type == 'Object':
        dump_datablock(bpy.data.objects[id], 1)
    if data_type == 'Collection':
        dump_datablock(bpy.data.collections[id], 4)
    if data_type == 'Scene':
        dump_datablock(bpy.data.scenes[id], 4)

def pull(keystore):
    global client_instance
    
    net_vars = bpy.context.scene.session_settings
    body = client_instance.property_map[keystore].body
    data_type = client_instance.property_map[keystore].mtype
    target = resolve_bpy_path(keystore)
    
    if target:
        target.is_updating = True

    if data_type == 'Object':
        load_object(target=target, data=body,
                    create=net_vars.load_data)
        global drawer
        drawer.draw()
    elif data_type == 'Mesh':
        load_mesh(target=target, data=body,
                    create=net_vars.load_data)
    elif data_type == 'Collection':
        load_collection(target=target, data=body,
                        create=net_vars.load_data)
    elif data_type == 'Material':
        load_material(target=target, data=body,
                        create=net_vars.load_data)
    elif data_type == 'Grease Pencil':
        load_gpencil(target=target, data=body,
                        create=net_vars.load_data)
    elif data_type == 'Scene':
        load_scene(target=target, data=body,
                    create=net_vars.load_data)
    elif 'Light' in data_type:
        load_light(target=target, data=body,
                    create=net_vars.load_data)
    elif data_type == 'Camera':
        load_default(target=target, data=body,
                        create=net_vars.load_data, type=mtype)
    elif data_type == 'client_instance':
        refresh_window()
    elif data_type == 'client_instanceObject':
            selected_objects = []

            for k, v in client_instance.property_map.items():
                if v.mtype == 'client_instanceObject':
                    if client_instance.id != v.id:
                        selected_objects.append(v.body['object'])

            for obj in bpy.data.objects:
                if obj.name in selected_objects:
                    obj.hide_select = True
                else:
                    obj.hide_select = False

            refresh_window()

recv_callbacks = [update_scene]
post_init_callbacks = [refresh_window]

def default_tick():
   
    # for op in bpy.context.window_manager.operators:
    #     try:
    #         if isinstance(op.uuid,tuple):
    #             op.uuid = str(uuid.uuid4())
    #     except Exception as e:
    #         print("error on {} {}".format(op.name,e))

    # if not push_tasks.empty():
    #     update = push_tasks.get()
    #     print(update)
    #     try:
    #         push(update[0],update[1])
    #     except Exception as e:
    #         print("push error: {}".format(e))


    # if not pull_tasks.empty():
    #     try:
    #         pull(pull_tasks.get())
    #     except Exception as e:
    #         print("pull error: {}".format(e))
    
    bpy.ops.session.refresh()

    return 0.5


def mesh_tick():
    mesh = get_update("Mesh")

    if mesh:
        upload_mesh(bpy.data.meshes[mesh])

    return 2


def object_tick():
    obj_name = get_update("Object")
    global client_instance

    if obj_name:
        if "Object/{}".format(obj_name) in client_instance.property_map.keys():
            dump_datablock_attibute(bpy.data.objects[obj_name], ['matrix_world'])
        else:
            dump_datablock(bpy.data.objects[obj_name], 1)

    return 0.1


def material_tick():
    return 2


def draw_tick():
    # drawing
    global drawer

    drawer.draw()

    # Upload
    upload_client_instance_position()
    return 0.2


def register_ticks():
    # REGISTER Updaters
    # bpy.app.timers.register(draw_tick)
    # bpy.app.timers.register(mesh_tick)
    # bpy.app.timers.register(object_tick)
    bpy.app.timers.register(default_tick)


def unregister_ticks():
    # REGISTER Updaters
    # global drawer
    # drawer.unregister_handlers()
    # bpy.app.timers.unregister(draw_tick)
    # bpy.app.timers.unregister(mesh_tick)
    # bpy.app.timers.unregister(object_tick)
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
        global client_instance, drawer

        net_settings = context.scene.session_settings
        # Scene setup
        if net_settings.session_mode == "CONNECT" and net_settings.clear_scene:
            clean_scene()

        # Session setup
        if net_settings.username == "DefaultUser":
            net_settings.username = "{}_{}".format(
                net_settings.username, randomStringDigits())

        username = str(context.scene.session_settings.username)


        client_instance = client.RCFClient()
        client_instance.connect(net_settings.username,"127.0.0.1",5555)
        

        # net_settings.is_running = True

        # drawer = net_draw.HUD(client_instance_instance=client_instance)

        register_ticks()
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
        global client_instance, client_keys

        client_keys = client_instance.list()
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

        client_instance.set(self.property_path)

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

        server = subprocess.Popen(['python','server.py'], shell=False, stdout=subprocess.PIPE)
        time.sleep(0.1)

        bpy.ops.session.join()

        if context.scene.session_settings.init_scene:
            init_datablocks()

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
        global client_instance, client_keys

        net_settings = context.scene.session_settings

        if server:
            server.kill()
            del server
            server = None
        if client_instance:
            client_instance.exit()
            del client_instance
            client_instance = None
            del client_keys
            client_keys = None
            # bpy.ops.asyncio.stop()
            net_settings.is_running = False

            unregister_ticks()
        else:
            logger.debug("No server/client_instance running.")

        return {"FINISHED"}


class session_settings(bpy.types.PropertyGroup):
    username = bpy.props.StringProperty(
        name="Username", default="user_{}".format(randomStringDigits()))
    ip = bpy.props.StringProperty(name="ip")
    port = bpy.props.IntProperty(name="5555")

    add_property_depth = bpy.props.IntProperty(
        name="add_property_depth", default=1)
    buffer = bpy.props.StringProperty(name="None")
    is_running = bpy.props.BoolProperty(name="is_running", default=False)
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


class session_snapview(bpy.types.Operator):
    bl_idname = "session.snapview"
    bl_label = "draw client_instances"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER"}

    target_client_instance = bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global client_instance

        area, region, rv3d = net_draw.view3d_find()

        for k, v in client_instance.property_map.items():
            if v.mtype == 'client_instance' and v.id.decode() == self.target_client_instance:
                rv3d.view_location = v.body['location'][1]
                rv3d.view_distance = 30.0
                return {"FINISHED"}

        return {"CANCELLED"}

        pass


# TODO: Rename to match official blender convention
classes = (
    session_join,
    session_refresh,
    session_add_property,
    session_stop,
    session_create,
    session_settings,
    session_remove_property,
    session_snapview,
)

def ordered(updates):
    # sorted = sorted(updates, key=lambda tup: SUPPORTED_TYPES.index(tup[1].id.bl_rna.name))
    uplist = [(SUPPORTED_TYPES.index(item[1].id.bl_rna.name),item[1].id.bl_rna.name,item[1].id.name) for item in updates.items()]
    uplist.sort(key=itemgetter(0))
    return uplist

def is_dirty(updates):
    global client_keys
    
    if client_keys:
        if len(client_keys) > 0:
            for u in updates:
                key = "{}/{}".format(u.id.bl_rna.name,u.id.name)

                if key not in client_keys:
                    return True

    return False

def depsgraph_update(scene):
    global client_instance
    
    if  client_instance and  client_instance.agent.is_alive():
        updates = bpy.context.depsgraph.updates
        # update_selected_object(bpy.context)
        push = False

        # Update selected object
    
        # for update in updates.items():
        #     updated_data = update[1]
            
        #     if updated_data.id.is_updating:
        #         updated_data.id.is_updating = False
        #         push = False
        #         break

        # if push:
            # if len(updates) is 1:
            #     updated_data = updates[0]
            #     if scene.session_settings.active_object and updated_data.id.name == scene.session_settings.active_object.name:
            #         if updated_data.is_updated_transform:
            #             add_update(updated_data.id.bl_rna.name, updated_data.id.name)
            # else:
        if is_dirty(updates) or push:
            for update in ordered(updates):
                if update[2] == "Master Collection":
                    pass
                elif update[1] in SUPPORTED_TYPES:
                    client_instance.set("{}/{}".format(update[1], update[2]))
            push = False

        
            # elif scene.session_settings.active_object and updated_data.id.name == scene.session_settings.active_object.name:
            #     if updated_data.is_updated_transform or updated_data.is_updated_geometry:
            #         add_update(updated_data.id.bl_rna.name, updated_data.id.name)
            # elif updated_data.id.bl_rna.name in [SUPPORTED_TYPES]:
            #     push_tasks.put((updated_data.id.bl_rna.name, updated_data.id.name))

        # for c in reversed(updates.items()):
        #     if c[1].is_updated_geometry:
        #         print("{} - {}".format(c[1].id.name,c[1].id.bl_rna.name))
        # for c in updates.items():
        #     if scene.session_settings.active_object:
        #         if c[1].id.name == scene.session_settings.active_object.name: 
        #             if c[1].is_updated_geometry:
        #                 add_update(c[1].id.bl_rna.name, c[1].id.name)
        #             elif c[1].is_updated_transform:
        #                 add_update(c[1].id.bl_rna.name, c[1].id.name)
        #             else:
        #                 pass
                    # print('other{}'.format(c[1].id.name))
                # if c[1].id.bl_rna.name == 'Material' or c[1].id.bl_rna.name== 'Shader Nodetree':
                # print(len(bpy.context.depsgraph.updates.items()))
                # data_name = c[1].id.name
                # if c[1].id.bl_rna.name == "Object":
                #     if data_name in bpy.data.objects.keys():
                #         found = False
                #         for k in client_instance.property_map.keys():
                #             if data_name in k:
                #                 found = True
                #                 break

                #         if not found:
                #             pass
                            # upload_mesh(bpy.data.objects[data_name].data)
                            # dump_datablock(bpy.data.objects[data_name], 1)
                            # dump_datablock(bpy.data.scenes[0], 4)
        

                    # dump_datablock(bpy.data.scenes[0],4)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.ID.is_dirty = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.session_settings = bpy.props.PointerProperty(
        type=session_settings)
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update)


def unregister():
    global server
    global client_instance, client_keys

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
    del bpy.types.ID.is_dirty

if __name__ == "__main__":
    register()
