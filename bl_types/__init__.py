__all__ = [
    'bl_object',
]  # Order here defines execution order

from . import *
from ..libs.replication.data import ReplicatedDataFactory

def types_to_register():
    return __all__

