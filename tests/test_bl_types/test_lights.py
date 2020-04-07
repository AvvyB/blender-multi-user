import pytest
import os
# from deepdiff import DeepDiff

from multi_user.bl_types.bl_light import BlLight
import bpy

@pytest.fixture
def load_test_file():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    bpy.ops.wm.open_mainfile(filepath=os.path.join(dir_path,"light.blend"))


def test_light(load_test_file):
    from jsondiff import diff
    blender_light = bpy.data.lights['point']
    light_dumper = BlLight(owner='None')
    sample_data = light_dumper._dump(blender_light)
    bpy.data.lights.remove(blender_light)

    test = light_dumper._construct(sample_data)
    light_dumper._load(sample_data, test)
    sample_2 = light_dumper._dump(test)
    assert diff(sample_data,test), False
