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

VERSION_EXPR = re.compile('\d+\.\d+\.\d+')

THIRD_PARTY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs")
DEFAULT_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "cache")
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
    subprocess.run([str(PYTHON_PATH), "-m", "ensurepip"])


def install_package(name, version):
    logging.info(f"installing {name} version...")
    subprocess.run([str(PYTHON_PATH), "-m", "pip", "install", f"{name}=={version}"])

def check_package_version(name, required_version):
    logging.info(f"Checking {name} version...")
    out = subprocess.run(f"{str(PYTHON_PATH)} -m pip show {name}", capture_output=True)

    version = VERSION_EXPR.search(out.stdout.decode())

    if version and version.group() == required_version:
        logging.info(f"{name} is up to date")
        return True
    else:
        logging.info(f"{name} need an update")
        return False

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


def setup(dependencies, python_path):
    global PYTHON_PATH, SUBPROCESS_DIR

    PYTHON_PATH = Path(python_path)
    SUBPROCESS_DIR = PYTHON_PATH.parent

    if not module_can_be_imported("pip"):
        install_pip()

    for package_name, package_version in dependencies:
        if not module_can_be_imported(package_name):
            install_package(package_name, package_version)
            module_can_be_imported(package_name)
        elif not check_package_version(package_name, package_version):
            install_package(package_name, package_version)
