import sys
import subprocess
import os
from pathlib import Path
import bpy

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"config")
APP_CONFIG =  os.path.join(CONFIG_DIR,"config.yaml")
THIRD_PARTY =  os.path.join(os.path.dirname(os.path.abspath(__file__)),"libs")
PYTHON_PATH = Path(bpy.app.binary_path_python)
SUBPROCESS_DIR = PYTHON_PATH.parent

def module_can_be_imported(name):
    try:
        __import__(name)
        return True
    except ModuleNotFoundError:
        return False


def get_package_install_directory():
    for path in sys.path:
        if os.path.basename(path) in ("dist-packages", "site-packages"):
            return path


def install_pip():
    # pip can not necessarily be imported into Blender after this
    get_pip_path = Path(__file__).parent / "libs" / "get-pip.py"
    subprocess.run([str(PYTHON_PATH), str(get_pip_path)], cwd=SUBPROCESS_DIR)


def install_package(name):
    target = get_package_install_directory()
    
    subprocess.run([str(PYTHON_PATH), "-m", "pip", "install",
                        name, '--target', target], cwd=SUBPROCESS_DIR)

def setup(dependencies):
    if not module_can_be_imported("pip"):
        install_pip()

    for dep in dependencies:
        if not module_can_be_imported(dep):
            install_package(dep)
