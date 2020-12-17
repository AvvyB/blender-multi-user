import os

import pytest
from deepdiff import DeepDiff

import bpy
import random
from multi_user.bl_types.bl_object import BlObject

# Removed 'BUILD' modifier because the seed doesn't seems to be
# correctly initialized (#TODO: report the bug)
MOFIFIERS_TYPES = [
    'DATA_TRANSFER', 'MESH_CACHE', 'MESH_SEQUENCE_CACHE',
    'NORMAL_EDIT', 'WEIGHTED_NORMAL', 'UV_PROJECT', 'UV_WARP',
    'VERTEX_WEIGHT_EDIT', 'VERTEX_WEIGHT_MIX',
    'VERTEX_WEIGHT_PROXIMITY', 'ARRAY', 'BEVEL', 'BOOLEAN',
    'DECIMATE', 'EDGE_SPLIT', 'MASK', 'MIRROR',
    'MULTIRES', 'REMESH', 'SCREW', 'SKIN', 'SOLIDIFY',
    'SUBSURF', 'TRIANGULATE',
    'WELD', 'WIREFRAME', 'ARMATURE', 'CAST', 'CURVE',
    'DISPLACE', 'HOOK', 'LAPLACIANDEFORM', 'LATTICE',
    'MESH_DEFORM', 'SHRINKWRAP', 'SIMPLE_DEFORM', 'SMOOTH',
    'CORRECTIVE_SMOOTH', 'LAPLACIANSMOOTH', 'SURFACE_DEFORM',
    'WARP', 'WAVE', 'CLOTH', 'COLLISION', 'DYNAMIC_PAINT',
    'EXPLODE', 'FLUID', 'OCEAN', 'PARTICLE_INSTANCE',
    'SOFT_BODY', 'SURFACE']

GP_MODIFIERS_TYPE = [
    'GP_ARRAY', 'GP_BUILD', 'GP_MIRROR', 'GP_MULTIPLY',
    'GP_SIMPLIFY', 'GP_SUBDIV', 'GP_ARMATURE',
    'GP_HOOK', 'GP_LATTICE', 'GP_NOISE', 'GP_OFFSET',
    'GP_SMOOTH', 'GP_THICK', 'GP_TIME', 'GP_COLOR',
    'GP_OPACITY', 'GP_TEXTURE', 'GP_TINT']

CONSTRAINTS_TYPES = [
    'CAMERA_SOLVER', 'FOLLOW_TRACK', 'OBJECT_SOLVER', 'COPY_LOCATION',
    'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS', 'LIMIT_DISTANCE',
    'LIMIT_LOCATION', 'LIMIT_ROTATION', 'LIMIT_SCALE', 'MAINTAIN_VOLUME',
    'TRANSFORM', 'TRANSFORM_CACHE', 'CLAMP_TO', 'DAMPED_TRACK', 'IK',
    'LOCKED_TRACK', 'STRETCH_TO', 'TRACK_TO', 'ACTION',
    'ARMATURE', 'CHILD_OF', 'FLOOR', 'FOLLOW_PATH', 'PIVOT', 'SHRINKWRAP']

# temporary disabled 'SPLINE_IK' until its fixed


def test_object(clear_blend):
    bpy.ops.mesh.primitive_cube_add(
        enter_editmode=False, align='WORLD', location=(0, 0, 0))

    datablock = bpy.data.objects[0]

    # Add modifiers
    for mod_type in MOFIFIERS_TYPES:
        datablock.modifiers.new(mod_type, mod_type)

    for mod_type in GP_MODIFIERS_TYPE:
        datablock.grease_pencil_modifiers.new(mod_type,mod_type)

    # Add constraints
    for const_type in CONSTRAINTS_TYPES:
        datablock.constraints.new(const_type)

    datablock.vertex_groups.new(name='vg')
    datablock.vertex_groups.new(name='vg1')
    datablock.shape_key_add(name='shape')
    datablock.shape_key_add(name='shape2')

    implementation = BlObject()
    expected = implementation._dump(datablock)
    bpy.data.objects.remove(datablock)

    test = implementation._construct(expected)
    implementation._load(expected, test)
    result = implementation._dump(test)

    assert not DeepDiff(expected, result)
