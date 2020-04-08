import os

import pytest
from deepdiff import DeepDiff

import bpy
import random
from multi_user.bl_types.bl_speaker import BlSpeaker

def test_speaker(clear_blend):
    bpy.ops.object.speaker_add()
    datablock = bpy.data.speakers[0]
    
    implementation = BlSpeaker()
    expected = implementation._dump(datablock)
    bpy.data.speakers.remove(datablock)

    test = implementation._construct(expected)
    implementation._load(expected, test)
    result = implementation._dump(test)

    assert not DeepDiff(expected, result)
