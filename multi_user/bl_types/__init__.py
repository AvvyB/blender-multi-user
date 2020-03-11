__all__ = [
    'bl_object',
    'bl_mesh',
    'bl_camera',
    'bl_collection',
    'bl_curve',
    'bl_gpencil',
    'bl_image',
    'bl_light',
    'bl_scene',
    'bl_material',
    'bl_library',
    'bl_armature',
    'bl_action',
    'bl_world',
    'bl_metaball',
    'bl_lattice',
    'bl_lightprobe',
    'bl_speaker',
    'bl_particle'
]  # Order here defines execution order

from . import *
from ..libs.replication.replication.data import ReplicatedDataFactory

def types_to_register():
    return __all__

