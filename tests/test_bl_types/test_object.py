import os

import pytest
from deepdiff import DeepDiff

import bpy
import random
from multi_user.bl_types.bl_object import BlObject

# Removed 'BUILD', 'SOFT_BODY' modifier because the seed doesn't seems to be
# correctly initialized (#TODO: report the bug)
MOFIFIERS_TYPES = [
    'DATA_TRANSFER', 'MESH_CACHE',
    'MESH_SEQUENCE_CACHE', 'NORMAL_EDIT', 'WEIGHTED_NORMAL',
    'UV_PROJECT', 'UV_WARP', 'VERTEX_WEIGHT_EDIT', 'VERTEX_WEIGHT_MIX',
    'VERTEX_WEIGHT_PROXIMITY', 'ARRAY', 'BEVEL', 'BOOLEAN', 'DECIMATE', 'EDGE_SPLIT', 'NODES', 'MASK', 'MIRROR',
    'MESH_TO_VOLUME', 'MULTIRES', 'REMESH', 'SCREW', 'SKIN', 'SOLIDIFY',
    'SUBSURF', 'TRIANGULATE', 'VOLUME_TO_MESH',
    'WELD', 'WIREFRAME', 'LINEART', 'ARMATURE', 'CAST', 'CURVE',
    'DISPLACE', 'HOOK', 'LAPLACIANDEFORM',
    'LATTICE', 'MESH_DEFORM', 'SHRINKWRAP', 'SIMPLE_DEFORM', 'SMOOTH',
    'CORRECTIVE_SMOOTH',
    'LAPLACIANSMOOTH', 'SURFACE_DEFORM', 'WARP', 'WAVE', 'VOLUME_DISPLACE',
    'CLOTH', 'COLLISION', 'DYNAMIC_PAINT', 'EXPLODE', 'FLUID', 'OCEAN',
    'PARTICLE_INSTANCE', 'SURFACE'
]
# 'PARTICLE_SYSTEM', 'SOFT_BODY', 'BUILD'

GP_MODIFIERS_TYPE = [
    'GREASE_PENCIL_VERTEX_WEIGHT_PROXIMITY', 'GREASE_PENCIL_COLOR',
    'GREASE_PENCIL_TINT', 'GREASE_PENCIL_OPACITY',
    'GREASE_PENCIL_VERTEX_WEIGHT_ANGLE', 'GREASE_PENCIL_TIME',
    'GREASE_PENCIL_TEXTURE', 'GREASE_PENCIL_ARRAY', 'GREASE_PENCIL_BUILD',
    'GREASE_PENCIL_LENGTH', 'GREASE_PENCIL_HOOK', 'GREASE_PENCIL_NOISE',
    'GREASE_PENCIL_OFFSET', 'GREASE_PENCIL_SMOOTH',
    'GREASE_PENCIL_THICKNESS', 'GREASE_PENCIL_LATTICE', 'GREASE_PENCIL_DASH',
    'GREASE_PENCIL_ARMATURE',
    'GREASE_PENCIL_SHRINKWRAP'
]

CONSTRAINTS_TYPES = [
    'CAMERA_SOLVER', 'FOLLOW_TRACK', 'OBJECT_SOLVER', 'COPY_LOCATION',
    'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS', 'LIMIT_DISTANCE',
    'LIMIT_LOCATION', 'LIMIT_ROTATION', 'LIMIT_SCALE', 'MAINTAIN_VOLUME',
    'TRANSFORM', 'TRANSFORM_CACHE', 'CLAMP_TO', 'DAMPED_TRACK', 'IK',
    'LOCKED_TRACK', 'STRETCH_TO', 'TRACK_TO', 'ACTION',
    'ARMATURE', 'CHILD_OF', 'FLOOR', 'FOLLOW_PATH', 'PIVOT', 'SHRINKWRAP']

# temporary disabled 'SPLINE_IK' until its fixed


def test_object(clear_blend, register_uuid):
    bpy.ops.mesh.primitive_cube_add(
        enter_editmode=False, align='WORLD', location=(0, 0, 0))

    datablock = bpy.data.objects[0]

    # Add modifiers
    for mod_type in MOFIFIERS_TYPES:
        datablock.modifiers.new(mod_type, mod_type)

    # Add constraints
    for const_type in CONSTRAINTS_TYPES:
        datablock.constraints.new(const_type)

    datablock.vertex_groups.new(name='vg')
    datablock.vertex_groups.new(name='vg1')
    datablock.shape_key_add(name='shape')
    datablock.shape_key_add(name='shape2')

    implementation = BlObject()
    expected = implementation.dump(datablock)
    bpy.data.objects.remove(datablock)

    test = implementation.construct(expected)
    implementation.load(expected, test)
    result = implementation.dump(test)
    print(DeepDiff(expected, result))
    assert not DeepDiff(expected, result)
