bl_info = {
    "name": "Multi-User",
    "author": "CUBE CREATIVE",
    "description": "",
    "blender": (2, 80, 0),
    "location": "",
    "warning": "",
    "category": "Collaboration"
}


import logging
import os
import random
import sys

import bpy
from bpy.app.handlers import persistent

from . import environment, utils
# from . import bl_types

DEPENDENCIES = {
    ("zmq","zmq"),
    ("umsgpack","umsgpack"),
    ("yaml","pyyaml"),
    ("jsondiff","jsondiff")
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#TODO: refactor config 
# UTILITY FUNCTIONS
def generate_supported_types():
    stype_dict = {'supported_types':{}}
    for type in bl_types.types_to_register():
        _type = getattr(bl_types, type)
        props = {}
        props['bl_delay_refresh']=_type.bl_delay_refresh
        props['bl_delay_apply']=_type.bl_delay_apply
        props['use_as_filter'] = False
        props['icon'] = _type.bl_icon
        props['auto_push']=_type.bl_automatic_push
        # stype_dict[type]['bl_delay_apply']=_type.bl_delay_apply
        stype_dict['supported_types'][_type.bl_rep_class.__name__] = props

    return stype_dict

def client_list_callback(scene, context):
    from . import operators
    from .bl_types.bl_user import BlUser
    
    items = [("Common", "Common", "")]

    username = bpy.context.window_manager.session.username
    cli = operators.client
    if cli:
        client_keys = cli.list(filter=BlUser)
        for k in client_keys:
                name = cli.get(uuid=k).buffer["name"]

                name_desc = name
                if name == username:
                    name_desc += " (self)"

                items.append((name, name_desc, ""))

    return items


def randomColor():
    r = random.random()
    v = random.random()
    b = random.random()
    return [r, v, b]


def save_session_config(self,context):
        config = environment.load_config()
        if "supported_types" not in config:
            config = generate_supported_types()
        config["username"] = self.username
        config["ip"] = self.ip
        config["port"] = self.port
        config["start_empty"] = self.start_empty
        config["enable_presence"] = self.enable_presence
        config["client_color"] = [self.client_color.r,self.client_color.g,self.client_color.b]
    
        rep_type = {}
        for bloc in self.supported_datablock:
            config["supported_types"][bloc.type_name]['bl_delay_refresh'] = bloc.bl_delay_refresh
            config["supported_types"][bloc.type_name]['bl_delay_apply'] = bloc.bl_delay_apply
            config["supported_types"][bloc.type_name]['use_as_filter'] = bloc.use_as_filter
            config["supported_types"][bloc.type_name]['icon'] = bloc.icon
            config["supported_types"][bloc.type_name]['auto_push'] = bloc.auto_push

        
        # Save out the configuration file
        environment.save_config(config)


class ReplicatedDatablock(bpy.types.PropertyGroup):
    '''name = StringProperty() '''
    type_name: bpy.props.StringProperty()
    bl_delay_refresh: bpy.props.FloatProperty()
    bl_delay_apply: bpy.props.FloatProperty()
    use_as_filter: bpy.props.BoolProperty(default=True)
    auto_push: bpy.props.BoolProperty(default=True)
    icon: bpy.props.StringProperty()

class SessionProps(bpy.types.PropertyGroup):
    username: bpy.props.StringProperty(
        name="Username",
        default="user_{}".format(utils.random_string_digits()),
        update=save_session_config
    )
    ip: bpy.props.StringProperty(
        name="ip",
        description='Distant host ip',
        default="127.0.0.1",
        update=save_session_config
        )
    user_uuid: bpy.props.StringProperty(
        name="user_uuid",
        default="None"
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
    outliner_filter: bpy.props.StringProperty(name="None")
    is_admin: bpy.props.BoolProperty(name="is_admin", default=False)
    init_scene: bpy.props.BoolProperty(name="init_scene", default=True)
    start_empty: bpy.props.BoolProperty(
        name="start_empty",
        default=True,
        update=save_session_config)
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
        items=client_list_callback)
    enable_presence: bpy.props.BoolProperty(
        name="enable_presence",
        description='Enable overlay drawing module',
        default=True,
        update=save_session_config
        )
    supported_datablock: bpy.props.CollectionProperty(
        type=ReplicatedDatablock,
        )
    session_filter: bpy.props.CollectionProperty(
        type=ReplicatedDatablock,
    )

    def load(self):
        config = environment.load_config()
        logger.info(config)
        if "username" in config.keys():
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
        if "supported_types" not in config:
            config = generate_supported_types()
        for datablock in config["supported_types"].keys():
            rep_value = self.supported_datablock.add()
            rep_value.name = datablock
            rep_value.type_name = datablock
            rep_value.bl_delay_refresh = config["supported_types"][datablock]['bl_delay_refresh']
            rep_value.bl_delay_apply = config["supported_types"][datablock]['bl_delay_apply']
            rep_value.icon = config["supported_types"][datablock]['icon']
            rep_value.auto_push = config["supported_types"][datablock]['auto_push']
            
    def save(self,context):
        config = environment.load_config()

        config["username"] = self.username
        config["ip"] = self.ip
        config["port"] = self.port
        config["start_empty"] = self.start_empty
        config["enable_presence"] = self.enable_presence
        config["client_color"] = [self.client_color.r,self.client_color.g,self.client_color.b]
        

        for bloc in self.supported_datablock:
            config["supported_types"][bloc.type_name]['bl_delay_refresh'] = bloc.bl_delay_refresh
            config["supported_types"][bloc.type_name]['bl_delay_apply'] = bloc.bl_delay_apply
            config["supported_types"][bloc.type_name]['use_as_filter'] = bloc.use_as_filter
            config["supported_types"][bloc.type_name]['icon'] = bloc.icon
            config["supported_types"][bloc.type_name]['auto_push'] = bloc.auto_push
        environment.save_config(config)    


classes = (
    ReplicatedDatablock,
    SessionProps,

)

libs = os.path.dirname(os.path.abspath(__file__))+"\\libs\\replication"

@persistent
def load_handler(dummy):
    import bpy
    bpy.context.window_manager.session.load()
    # Generate ordered replicate types
    
    save_session_config(bpy.context.window_manager.session,bpy.context)


def register():
    if libs not in sys.path:
        sys.path.append(libs)
    
    environment.setup(DEPENDENCIES,bpy.app.binary_path_python)

    from . import operators
    from . import ui

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.session = bpy.props.PointerProperty(
        type=SessionProps)
    bpy.types.ID.uuid = bpy.props.StringProperty(default="")
    bpy.context.window_manager.session.load()
    save_session_config(bpy.context.window_manager.session,bpy.context)
    operators.register()
    ui.register()
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    from . import operators
    from . import ui

    ui.unregister()
    operators.unregister()

    del bpy.types.WindowManager.session

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
