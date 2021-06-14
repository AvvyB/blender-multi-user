import os

import pytest
from deepdiff import DeepDiff

import bpy
import random
from multi_user.bl_types.bl_volume import BlVolume

def test_volume(clear_blend):
    datablock = bpy.data.volumes.new("Test")

    implementation = BlVolume()
    expected = implementation.dump(datablock)
    bpy.data.volumes.remove(datablock)

    test = implementation.construct(expected)
    implementation.load(expected, test)
    result = implementation.dump(test)

    assert not DeepDiff(expected, result)
