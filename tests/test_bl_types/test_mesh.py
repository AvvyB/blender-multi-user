import os

import pytest
from deepdiff import DeepDiff

import bpy
import random
from multi_user.bl_types.bl_mesh import BlMesh

@pytest.mark.parametrize('mesh_type', ['EMPTY','FILLED'])
def test_mesh(clear_blend, mesh_type):
    if mesh_type == 'FILLED':
        bpy.ops.mesh.primitive_monkey_add()
    elif mesh_type == 'EMPTY':
        bpy.data.meshes.new('empty_mesh')

    datablock = bpy.data.meshes[0]
    
    # Test
    implementation = BlMesh()
    expected = implementation.dump(datablock)
    bpy.data.meshes.remove(datablock)

    test = implementation.construct(expected)
    implementation.load(expected, test)
    result = implementation.dump(test)

    assert not DeepDiff(expected, result)
