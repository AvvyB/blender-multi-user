import os

import pytest
from deepdiff import DeepDiff

import bpy
from multi_user.bl_types.bl_metaball import BlMetaball


@pytest.mark.parametrize('metaballs_type', ['PLANE','CAPSULE','BALL','ELLIPSOID','CUBE'])
def test_metaball(clear_blend, metaballs_type):
    bpy.ops.object.metaball_add(type=metaballs_type)

    datablock = bpy.data.metaballs[0]
    dumper = BlMetaball()
    expected = dumper.dump(datablock)
    bpy.data.metaballs.remove(datablock)

    test = dumper.construct(expected)
    dumper.load(expected, test)
    result = dumper.dump(test)

    assert not DeepDiff(expected, result)
