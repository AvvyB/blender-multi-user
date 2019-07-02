bl_info = {
    "name": "Multi-User",
    "author": "CUBE CREATIVE",
    "description": "",
    "blender": (2, 80, 0),
    "location": "",
    "warning": "",
    "category": "Collaboration"
}


import addon_utils
import logging
import random
import string
import sys
import os
import bpy
from . import environment


DEPENDENCIES = {
    "zmq",
    "umsgpack",
    "yaml"
}


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# UTILITY FUNCTIONS
def client_list_callback(scene, context):
    from . import client
    
    items = [("Common", "Common", "")]

    username = bpy.context.window_manager.session.username

    if client.instance:
        client_keys = client.instance.list()
        for k in client_keys:
            if 'Client' in k[0]:
                name = k[1]

                if name == username:
                    name += " (self)"

                items.append((name, name, ""))

    return items


def randomStringDigits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


def randomColor():
    r = random.random()
    v = random.random()
    b = random.random()
    return [r, v, b]


def save_session_config(self,context):
        config = environment.load_config()

        config["username"] = self.username
        config["ip"] = self.ip
        config["port"] = self.port
        config["start_empty"] = self.start_empty
        config["enable_presence"] = self.enable_presence
        config["client_color"] = [self.client_color.r,self.client_color.g,self.client_color.b]
        
        rep_type = {}
        for bloc in self.supported_datablock:
            config["replicated_types"][bloc.type_name] = bloc.is_replicated

        # config["replicated_types"] = rep_type
        
        environment.save_config(config)

class ReplicatedDatablock(bpy.types.PropertyGroup):
    '''name = StringProperty() '''
    type_name: bpy.props.StringProperty()
    is_replicated: bpy.props.BoolProperty()

class SessionProps(bpy.types.PropertyGroup):
    username: bpy.props.StringProperty(
        name="Username",
        default="user_{}".format(randomStringDigits()),
        update=save_session_config
    )
    ip: bpy.props.StringProperty(
        name="ip",
        description='Distant host ip',
        default="127.0.0.1",
        update=save_session_config
        )
    port: bpy.props.IntProperty(
        name="port",
        description='Distant host port',
        default=5555,
        update=save_session_config
        )
    add_property_depth: bpy.props.IntProperty(
        name="add_property_depth",
        default=1
        )
    buffer: bpy.props.StringProperty(name="None")
    is_admin: bpy.props.BoolProperty(name="is_admin", default=False)
    load_data: bpy.props.BoolProperty(name="load_data", default=True)
    init_scene: bpy.props.BoolProperty(name="load_data", default=True)
    start_empty: bpy.props.BoolProperty(
        name="start_empty",
        default=False,
        update=save_session_config
        )
    update_frequency: bpy.props.FloatProperty(
        name="update_frequency",
        default=0.008
        )
    active_object: bpy.props.PointerProperty(
        name="active_object", type=bpy.types.Object)
    session_mode: bpy.props.EnumProperty(
        name='session_mode',
        description='session mode',
        items={
            ('HOST', 'hosting', 'host a session'),
            ('CONNECT', 'connexion', 'connect to a session')},
        default='HOST')
    client_color: bpy.props.FloatVectorProperty(
        name="client_instance_color",
        subtype='COLOR',
        default=randomColor(),
        update=save_session_config)
    clients: bpy.props.EnumProperty(
        name="clients",
        description="client enum",
        items=client_list_callback
    )
    enable_presence: bpy.props.BoolProperty(
        name="enable_presence",
        description='Enable overlay drawing module',
        default=True,
        update=save_session_config
        )
    supported_datablock: bpy.props.CollectionProperty(
        type=ReplicatedDatablock,
       
        )

    def load(self):
        config = environment.load_config()
        logger.info(config)
        if "username" in config:
            self.username = config["username"]
            self.ip = config["ip"]
            self.port = config["port"]
            self.start_empty = config["start_empty"]
            self.enable_presence = config["enable_presence"]
            self.client_color = config["client_color"]
        else:
            logger.error("Fail to read user config")
        
        if len(self.supported_datablock)>0:
            self.supported_datablock.clear()
        for datablock,enabled in config["replicated_types"].items():
            rep_value = self.supported_datablock.add()
            rep_value.type_name = datablock
            rep_value.is_replicated = enabled

    def save(self,context):
        config = environment.load_config()

        config["username"] = self.username
        config["ip"] = self.ip
        config["port"] = self.port
        config["start_empty"] = self.start_empty
        config["enable_presence"] = self.enable_presence
        config["client_color"] = [self.client_color.r,self.client_color.g,self.client_color.b]
        
        rep_type = {}
        for bloc in self.supported_datablock:
            print(bloc.type_name)
            config["replicated_types"][bloc.type_name] = bloc.is_replicated

        
        environment.save_config(config)    


        
    

classes = (
    ReplicatedDatablock,
    SessionProps

)


def register():
    environment.setup(DEPENDENCIES,bpy.app.binary_path_python)

    from . import operators
    from . import ui

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.ID.id = bpy.props.StringProperty(default="None")
    bpy.types.ID.is_dirty = bpy.props.BoolProperty(default=False)
    bpy.types.WindowManager.session = bpy.props.PointerProperty(
        type=SessionProps)

    bpy.context.window_manager.session.load()
    save_session_config(bpy.context.window_manager.session,bpy.context)
    operators.register()
    ui.register()


def unregister():
    from . import operators
    from . import ui

    ui.unregister()
    operators.unregister()

    del bpy.types.WindowManager.session
    del bpy.types.ID.id
    del bpy.types.ID.is_dirty

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
