import os
import subprocess
import sys
from pathlib import Path
import logging
import yaml
import collections

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
CONFIG = os.path.join(CONFIG_DIR, "app.yaml")

THIRD_PARTY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs")
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
PYTHON_PATH = None
SUBPROCESS_DIR = None
DEFAULT_CONFIG = {
    "replicated_types": {
        'Client': True,
        'Image': True,
        'Texture': True,
        'Curve': True,
        'Material': True,
        'Light': True,
        'SunLight': True,
        'SpotLight': True,
        'AreaLight': True,
        'PointLight': True,
        'Camera': True,
        'Mesh': True,
        'Armature': True,
        'GreasePencil': True,
        'Object': True,
        'Action': True,
        'Collection': True,
        'Scene': True
    }
}

ORDERED_TYPES = [
        'Image',
        'Texture',
        'Curve',
        'Material',
        'Light',
        'SunLight',
        'SpotLight',
        'AreaLight',
        'PointLight',
        'Camera',
        'Mesh',
        'Armature',
        'GreasePencil',
        'Object',
        'Action',
        'Collection',
        'Scene',
]

rtypes = []

def load_config():
    try:
        with open(CONFIG, 'r') as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        logger.info("no config")

    return DEFAULT_CONFIG

def genereate_replicated_types(replicated_types):
    for t in ORDERED_TYPES:
        if replicated_types[t]:
            rtypes.append(t)


def save_config(config):
    logger.info("saving config")
    with open(CONFIG, 'w') as outfile:
        yaml.dump(config, outfile, default_flow_style=False)


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


def setup(dependencies, python_path):
    global PYTHON_PATH, SUBPROCESS_DIR

    PYTHON_PATH = Path(python_path)
    SUBPROCESS_DIR = PYTHON_PATH.parent


    if not module_can_be_imported("pip"):
        install_pip()

    for dep in dependencies:
        if not module_can_be_imported(dep):
            install_package(dep)
