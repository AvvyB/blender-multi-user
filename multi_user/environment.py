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


THIRD_PARTY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs")
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
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


def install_package(name):
    logging.debug(f"Using {PYTHON_PATH} for installation")
    subprocess.run([str(PYTHON_PATH), "-m", "pip", "install", name])


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
            module_can_be_imported(package_name)
