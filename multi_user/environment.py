import collections
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

THIRD_PARTY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs")
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
PYTHON_PATH = None
SUBPROCESS_DIR = None


rtypes = []

def module_can_be_imported(name):
    try:
        __import__(name)
        return True
    except ModuleNotFoundError:
        return False


def install_pip():
    # pip can not necessarily be imported into Blender after this
    get_pip_path = Path(__file__).parent / "libs" / "get-pip.py"
    subprocess.run([str(PYTHON_PATH), str(get_pip_path)], cwd=SUBPROCESS_DIR)


def install_package(name):
    subprocess.run([str(PYTHON_PATH), "-m", "pip", "install",
                    name], cwd=SUBPROCESS_DIR)

def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def setup(dependencies, python_path):
    global PYTHON_PATH, SUBPROCESS_DIR

    PYTHON_PATH = Path(python_path)
    SUBPROCESS_DIR = PYTHON_PATH.parent

    if not module_can_be_imported("pip"):
        install_pip()

    for module_name, package_name in dependencies:
        if not module_can_be_imported(module_name):
            install_package(package_name)
