import os

import pytest
from deepdiff import DeepDiff

import bpy
from multi_user.bl_types.bl_camera import BlCamera


@pytest.mark.parametrize('camera_type', ['PANO','PERSP','ORTHO'])
def test_camera(clear_blend, camera_type):
    bpy.ops.object.camera_add()

    datablock = bpy.data.cameras[0]
    datablock.type = camera_type

    camera_dumper = BlCamera()
    expected = camera_dumper._dump(datablock)
    bpy.data.cameras.remove(datablock)

    test = camera_dumper._construct(expected)
    camera_dumper._load(expected, test)
    result = camera_dumper._dump(test)

    assert not DeepDiff(expected, result)
