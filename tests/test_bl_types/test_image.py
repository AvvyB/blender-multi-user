import os

import pytest
from deepdiff import DeepDiff

import bpy
import random
from multi_user.bl_types.bl_image import BlImage

def test_image(clear_blend):
    datablock = bpy.data.images.new('asd',2000,2000)
    
    implementation = BlImage()
    expected = implementation._dump(datablock)
    bpy.data.images.remove(datablock)

    test = implementation._construct(expected)
    implementation._load(expected, test)
    result = implementation._dump(test)

    assert not DeepDiff(expected, result)
