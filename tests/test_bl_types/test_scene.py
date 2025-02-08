import os

import pytest
from deepdiff import DeepDiff

import bpy
import random
from multi_user.bl_types.bl_scene import BlScene
# from multi_user.utils import get_preferences

def test_scene(clear_blend, register_uuid):
    # get_preferences().sync_flags.sync_render_settings = True

    datablock = bpy.data.scenes.new("toto")
    datablock.timeline_markers.new('toto', frame=10)
    datablock.timeline_markers.new('tata', frame=1)
    datablock.view_settings.use_curve_mapping = True
    # Test
    implementation = BlScene()
    expected = implementation.dump(datablock)
    bpy.data.scenes.remove(datablock)

    test = implementation.construct(expected)
    implementation.load(expected, test)
    result = implementation.dump(test)

    assert not DeepDiff(expected, result)
