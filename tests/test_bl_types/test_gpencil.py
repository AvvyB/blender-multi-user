import os

import pytest
from deepdiff import DeepDiff

import bpy
from multi_user.bl_types.bl_gpencil import BlGpencil


def test_gpencil(clear_blend):
    bpy.ops.object.gpencil_add(type='MONKEY')

    datablock = bpy.data.grease_pencils[0]

    implementation = BlGpencil()
    expected = implementation._dump(datablock)
    bpy.data.grease_pencils.remove(datablock)

    test = implementation._construct(expected)
    implementation._load(expected, test)
    result = implementation._dump(test)

    assert not DeepDiff(expected, result)
