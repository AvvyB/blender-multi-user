__all__ = [
    'bl_object',
    'bl_mesh',
]  # Order here defines execution order

from . import *
from ..libs.replication.data import ReplicatedDataFactory

def types_to_register():
    return __all__

