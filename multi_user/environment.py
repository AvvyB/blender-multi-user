# ##### BEGIN GPL LICENSE BLOCK #####
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


import collections
import logging
import os
import subprocess
import sys
from pathlib import Path
import socket
import re
import bpy

VERSION_EXPR = re.compile('\d+.\d+.\d+')
DEFAULT_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "cache")
REPLICATION_DEPENDENCIES = {
    "zmq",
    "deepdiff"
}
LIBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs")
REPLICATION = os.path.join(LIBS,"replication")


rtypes = []


def module_can_be_imported(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ModuleNotFoundError:
        return False


def install_pip(python_path):
    # pip can not necessarily be imported into Blender after this
    subprocess.run([str(python_path), "-m", "ensurepip"])


def install_requirements(python_path:str, module_requirement: str, install_dir: str):
    logging.info(f"Installing {module_requirement} dependencies in {install_dir}")
    env = os.environ
    if "PIP_REQUIRE_VIRTUALENV" in env:
        # PIP_REQUIRE_VIRTUALENV is an env var to ensure pip cannot install packages outside a virtual env
        # https://docs.python-guide.org/dev/pip-virtualenv/
        # But since Blender's pip is outside of a virtual env, it can block our packages installation, so we unset the
        # env var for the subprocess.
        env = os.environ.copy()
        del env["PIP_REQUIRE_VIRTUALENV"]
    subprocess.run([str(python_path), "-m", "pip", "install", "-r", f"{install_dir}/{module_requirement}/requirements.txt", "-t", install_dir], env=env)


def get_ip():
    """
    Retrieve the main network interface IP.

    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def check_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def setup_paths(paths: list):
    """ Add missing path to sys.path
    """ 
    for path in paths:
        if path not in sys.path:
            logging.debug(f"Adding {path} dir to the path.")
            sys.path.insert(0, path)


def remove_paths(paths: list):
    """ Remove list of path from sys.path
    """
    for path in paths:
        if path in sys.path:
            logging.debug(f"Removing {path} dir from the path.")
            sys.path.remove(path)
      

def register():
    if bpy.app.version >= (2,91,0):
            python_binary_path = sys.executable
    else:
        python_binary_path = bpy.app.binary_path_python

    python_path = Path(python_binary_path)

    for module_name in list(sys.modules.keys()):
        if 'replication' in module_name:
            del sys.modules[module_name]

    setup_paths([LIBS, REPLICATION])

    if not module_can_be_imported("pip"):
        install_pip(python_path)

    deps_not_installed = [package_name for package_name in REPLICATION_DEPENDENCIES if not module_can_be_imported(package_name)]
    if any(deps_not_installed):
        install_requirements(python_path, module_requirement='replication', install_dir=LIBS)
    

def unregister():
    remove_paths([REPLICATION, LIBS])