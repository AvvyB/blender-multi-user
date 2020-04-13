import os

import pytest
from deepdiff import DeepDiff

import bpy
from multi_user.bl_types.bl_lightprobe import BlLightprobe


@pytest.mark.skipif(bpy.app.version[1] < 83, reason="requires blender 2.83 or higher")
@pytest.mark.parametrize('lightprobe_type', ['PLANAR','GRID','CUBEMAP'])
def test_lightprobes(clear_blend, lightprobe_type):
    bpy.ops.object.lightprobe_add(type=lightprobe_type)

    blender_light = bpy.data.lightprobes[0]
    lightprobe_dumper = BlLightprobe()
    expected = lightprobe_dumper._dump(blender_light)
    bpy.data.lightprobes.remove(blender_light)

    test = lightprobe_dumper._construct(expected)
    lightprobe_dumper._load(expected, test)
    result = lightprobe_dumper._dump(test)

    assert not DeepDiff(expected, result)
