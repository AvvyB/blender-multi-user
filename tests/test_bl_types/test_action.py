import os

import pytest
from deepdiff import DeepDiff

import bpy
import random
from multi_user.bl_types.bl_action import BlAction

INTERPOLATION = ['CONSTANT', 'LINEAR', 'BEZIER', 'SINE', 'QUAD', 'CUBIC', 'QUART', 'QUINT', 'EXPO', 'CIRC', 'BACK', 'BOUNCE', 'ELASTIC']
FMODIFIERS = ['GENERATOR', 'FNGENERATOR', 'ENVELOPE', 'CYCLES', 'NOISE', 'LIMITS', 'STEPPED']

# @pytest.mark.parametrize('blendname', ['test_action.blend'])
def test_action(clear_blend):
    # Generate a random action
    datablock = bpy.data.actions.new("sdsad")
    fcurve_sample = datablock.fcurves.new('location')
    fcurve_sample.keyframe_points.add(100)
    datablock.id_root = 'MESH'

    for i, point in enumerate(fcurve_sample.keyframe_points):
        point.co[0] = i
        point.co[1] = random.randint(-10,10)
        point.interpolation = INTERPOLATION[random.randint(0, len(INTERPOLATION)-1)]

    for mod_type in FMODIFIERS:
        fcurve_sample.modifiers.new(mod_type)

    bpy.ops.mesh.primitive_plane_add()
    bpy.data.objects[0].animation_data_create()
    bpy.data.objects[0].animation_data.action = datablock

    # Test
    implementation = BlAction()
    expected = implementation._dump(datablock)
    bpy.data.actions.remove(datablock)

    test = implementation._construct(expected)
    implementation._load(expected, test)
    result = implementation._dump(test)

    assert not DeepDiff(expected, result)
