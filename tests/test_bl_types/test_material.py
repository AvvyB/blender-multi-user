import os

import pytest
from deepdiff import DeepDiff

import bpy
from multi_user.bl_types.bl_material import BlMaterial


def test_material(clear_blend):
    nodes_types = [node.bl_rna.identifier for node in bpy.types.ShaderNode.__subclasses__()]
    
    datablock = bpy.data.materials.new("test")
    datablock.use_nodes = True
    bpy.data.materials.create_gpencil_data(datablock)
    
    for ntype in nodes_types:
        datablock.node_tree.nodes.new(ntype) 

    implementation = BlMaterial()
    expected = implementation._dump(datablock)
    bpy.data.materials.remove(datablock)

    test = implementation._construct(expected)
    implementation._load(expected, test)
    result = implementation._dump(test)

    assert not DeepDiff(expected, result)
