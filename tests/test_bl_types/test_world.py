import os

import pytest
from deepdiff import DeepDiff

import bpy
import random
from multi_user.bl_types.bl_world import BlWorld

def test_world(clear_blend):
    datablock = bpy.data.worlds.new('test')
    datablock.use_nodes = True
    
    implementation = BlWorld()
    expected = implementation.dump(datablock)
    bpy.data.worlds.remove(datablock)

    test = implementation.construct(expected)
    implementation.load(expected, test)
    result = implementation.dump(test)

    assert not DeepDiff(expected, result)
