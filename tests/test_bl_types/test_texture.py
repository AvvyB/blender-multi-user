import os

import pytest
from deepdiff import DeepDiff

import bpy
import random
from multi_user.bl_types.bl_texture import BlTexture

TEXTURE_TYPES = ['NONE', 'BLEND', 'CLOUDS', 'DISTORTED_NOISE', 'IMAGE', 'MAGIC', 'MARBLE', 'MUSGRAVE', 'NOISE', 'STUCCI', 'VORONOI', 'WOOD']

@pytest.mark.parametrize('texture_type', TEXTURE_TYPES)
def test_texture(clear_blend, texture_type):
    datablock = bpy.data.textures.new('test', texture_type)

    implementation = BlTexture()
    expected = implementation.dump(datablock)
    bpy.data.textures.remove(datablock)

    test = implementation.construct(expected)
    implementation.load(expected, test)
    result = implementation.dump(test)

    assert not DeepDiff(expected, result)
