from pathlib import Path
import addon_utils
import random
import string
import subprocess
import sys
import os
import bpy

bl_info = {
    "name": "Multi-User ",
    "author": "CUBE",
    "description": "",
    "blender": (2, 80, 0),
    "location": "",
    "warning": "",
    "category": "Collaboration"
}



def module_can_be_imported(name):
    try:
        __import__(name)
        return True
    except ModuleNotFoundError:
        return False

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


def get_package_install_directory():
    for path in sys.path:
        if os.path.basename(path) in ("dist-packages", "site-packages"):
            return path


class SessionProps(bpy.types.PropertyGroup):
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
        default=5554)

    add_property_depth: bpy.props.IntProperty(
        name="add_property_depth",
        default=1)
    buffer: bpy.props.StringProperty(name="None")
    is_admin: bpy.props.BoolProperty(name="is_admin", default=False)
    load_data: bpy.props.BoolProperty(name="load_data", default=True)
    init_scene: bpy.props.BoolProperty(name="load_data", default=True)
    clear_scene: bpy.props.BoolProperty(name="clear_scene", default=False)
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
    SessionProps,
}


python_path = Path(bpy.app.binary_path_python)
cwd_for_subprocesses = python_path.parent
target = get_package_install_directory()


def install_pip():
    # pip can not necessarily be imported into Blender after this
    get_pip_path = Path(__file__).parent / "libs" / "get-pip.py"
    subprocess.run([str(python_path), str(get_pip_path)], cwd=cwd_for_subprocesses)


def install_package(name):
    target = get_package_install_directory()
    subprocess.run([str(python_path), "-m", "pip", "install", name, '--target', target], cwd=cwd_for_subprocesses)


def register():
    if not module_can_be_imported("pip"):
        install_pip()
       
    if not module_can_be_imported("zmq"):
        subprocess.run([str(python_path), "-m", "pip", "install",
                        "zmq", '--target', target], cwd=cwd_for_subprocesses)

    from . import operators
    from . import ui

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.ID.id = bpy.props.StringProperty(default="None")
    bpy.types.ID.is_dirty = bpy.props.BoolProperty(default=False)
    bpy.types.WindowManager.session = bpy.props.PointerProperty(
        type=SessionProps)

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
