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


def preload_modules():
    from . import wheels

    wheels.load_wheel_global("ordered_set", "ordered_set")
    wheels.load_wheel_global("deepdiff", "deepdiff")
    wheels.load_wheel_global("replication", "replication")
    wheels.load_wheel_global("zmq", "pyzmq", match_platform=True)



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
    check_dir(DEFAULT_CACHE_DIR)

def unregister():
    pass