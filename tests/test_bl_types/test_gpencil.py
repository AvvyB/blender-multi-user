import os

import pytest
from deepdiff import DeepDiff

import bpy
from multi_user.bl_types.bl_gpencil3 import BlGpencil3


def test_gpencil3(clear_blend, register_uuid):
    bpy.ops.object.grease_pencil_add(type='MONKEY')

    datablock = bpy.data.grease_pencils_v3[0]

    implementation = BlGpencil3()
    expected = implementation.dump(datablock)
    bpy.data.grease_pencils_v3.remove(datablock)

    test = implementation.construct(expected)
    implementation.load(expected, test)
    result = implementation.dump(test)

    assert not DeepDiff(expected, result)
