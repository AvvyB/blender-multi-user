import os

import pytest
from deepdiff import DeepDiff

import bpy
import random
from multi_user.bl_types.bl_armature import BlArmature


def test_armature(clear_blend, register_uuid):
    bpy.ops.object.armature_add()
    datablock = bpy.data.armatures[0]

    implementation = BlArmature()
    expected = implementation.dump(datablock)
    bpy.data.armatures.remove(datablock)

    test = implementation.construct(expected)
    implementation.load(expected, test)
    result = implementation.dump(test)

    assert not DeepDiff(expected, result)
