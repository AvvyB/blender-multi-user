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
import bpy
import addon_utils
from pathlib import Path

python_path = Path(bpy.app.binary_path_python)
cwd_for_subprocesses = python_path.parent

def get_package_install_directory():
    for path in sys.path:
        if os.path.basename(path) in ("dist-packages", "site-packages"):
            return path

try:
    import zmq
except:
    target = get_package_install_directory()
    subprocess.run([str(python_path), "-m", "pip", "install", "zmq", '--target', target], cwd=cwd_for_subprocesses)

from . import operators
from . import ui

def register():
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()

    