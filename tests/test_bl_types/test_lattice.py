import os

import pytest
from deepdiff import DeepDiff

import bpy
from multi_user.bl_types.bl_lattice import BlLattice


def test_lattice(clear_blend):
    bpy.ops.object.add(type='LATTICE', enter_editmode=False, align='WORLD', location=(0, 0, 0))

    datablock = bpy.data.lattices[0]

    implementation = BlLattice()
    expected = implementation.dump(datablock)
    bpy.data.lattices.remove(datablock)

    test = implementation.construct(expected)
    implementation.load(expected, test)
    result = implementation.dump(test)

    assert not DeepDiff(expected, result)
