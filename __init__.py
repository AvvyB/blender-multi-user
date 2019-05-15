bl_info = {
    "name" : "rcf",
    "author" : "CUBE",
    "description" : "",
    "blender" : (2, 80, 0),
    "location" : "",
    "warning" : "",
    "category" : "Collaboration"
}


import bpy
import os
import sys
import subprocess
import string
import random
import bpy
import addon_utils
from pathlib import Path

python_path = Path(bpy.app.binary_path_python)
cwd_for_subprocesses = python_path.parent


# UTILITY FUNCTIONS
def client_list_callback(scene, context):
    global client_keys
    items = [("Common", "Common", "")]

    username = bpy.context.window_manager.session.username 

    if client_keys:
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


def get_package_install_directory():
    for path in sys.path:
        if os.path.basename(path) in ("dist-packages", "site-packages"):
            return path


class RCFSessionProps(bpy.types.PropertyGroup):
    username: bpy.props.StringProperty(
        name="Username",
        default="user_{}".format(randomStringDigits())
        )
    ip: bpy.props.StringProperty(
        name="ip",
        description='Distant host ip',
        default="127.0.0.1")
    port: bpy.props.IntProperty(
        name="port",
        description='Distant host port',
        default=5555)

    add_property_depth: bpy.props.IntProperty(
        name="add_property_depth",
        default=1)
    buffer: bpy.props.StringProperty(name="None")
    is_admin: bpy.props.BoolProperty(name="is_admin", default=False)
    load_data: bpy.props.BoolProperty(name="load_data", default=True)
    init_scene: bpy.props.BoolProperty(name="load_data", default=True)
    clear_scene: bpy.props.BoolProperty(name="clear_scene", default=True)
    update_frequency: bpy.props.FloatProperty(
        name="update_frequency", default=0.008)
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
        default=randomColor())
    clients: bpy.props.EnumProperty(
        name="clients",
        description="client enum",
        items=client_list_callback
    )
    enable_draw: bpy.props.BoolProperty(
        name="enable_draw",
        description='Enable overlay drawing module',
        default=True)

classes = {
    RCFSessionProps,
}

def register():
    try:
        import zmq
    except:
        target = get_package_install_directory()
        subprocess.run([str(python_path), "-m", "pip", "install", "zmq", '--target', target], cwd=cwd_for_subprocesses)

    from . import operators
    from . import ui

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.ID.id = bpy.props.StringProperty(default="None")
    bpy.types.ID.is_dirty = bpy.props.BoolProperty(default=False)
    bpy.types.WindowManager.session = bpy.props.PointerProperty(
        type=RCFSessionProps)

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

    for cls in classes:
        bpy.utils.unregister_class(cls)
