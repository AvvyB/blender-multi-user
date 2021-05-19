import os

import pytest
from deepdiff import DeepDiff

import bpy
from multi_user.bl_types.bl_light import BlLight


@pytest.mark.parametrize('light_type', ['SPOT','SUN','POINT','AREA'])
def test_light(clear_blend, light_type):
    bpy.ops.object.light_add(type=light_type)

    blender_light = bpy.data.lights[0]
    light_dumper = BlLight()
    expected = light_dumper.dump(blender_light)
    bpy.data.lights.remove(blender_light)

    test = light_dumper.construct(expected)
    light_dumper.load(expected, test)
    result = light_dumper.dump(test)

    assert not DeepDiff(expected, result)
