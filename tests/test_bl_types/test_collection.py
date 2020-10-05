import os

import pytest
from deepdiff import DeepDiff
from uuid import uuid4
import bpy
import random
from multi_user.bl_types.bl_collection import BlCollection

def test_collection(clear_blend):
    # Generate a collection with childrens and a cube
    datablock = bpy.data.collections.new("root")
    datablock.uuid = str(uuid4())
    s1 = bpy.data.collections.new("child")
    s1.uuid = str(uuid4())
    s2 = bpy.data.collections.new("child2")
    s2.uuid = str(uuid4())
    datablock.children.link(s1)
    datablock.children.link(s2)

    bpy.ops.mesh.primitive_cube_add()
    datablock.objects.link(bpy.data.objects[0])

    # Test
    implementation = BlCollection()
    expected = implementation._dump(datablock)
    bpy.data.collections.remove(datablock)

    test = implementation._construct(expected)
    implementation._load(expected, test)
    result = implementation._dump(test)

    assert not DeepDiff(expected, result)
