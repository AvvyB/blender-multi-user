import os

import pytest

import bpy
from multi_user import register, unregister


@pytest.fixture()
def register_uuid():
    """ Register the addon
    """
    bpy.types.ID.uuid = bpy.props.StringProperty(
        default="", options={"HIDDEN", "SKIP_SAVE"}
    )


@pytest.fixture
def clear_blend():
    """ Remove all datablocks of a blend
    """
    for type_name in dir(bpy.data):
        try:
            type_collection = getattr(bpy.data, type_name)
            for item in type_collection:
                type_collection.remove(item)
        except Exception:
            continue


@pytest.fixture
def load_blendfile(blendname):
    print(f"loading {blendname}")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    bpy.ops.wm.open_mainfile(filepath=os.path.join(dir_path, blendname))
