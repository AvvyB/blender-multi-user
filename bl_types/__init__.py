__all__ = [
    'bl_object',
]  # Order here defines execution order

from . import *
from ..libs.replication.data import ReplicatedDataFactory

def types_to_register():
    return __all__

def bl_types_factory():
    bpy_factory = ReplicatedDataFactory()
    module = __import__(__name__)

    for type in types_to_register():
        _type = getattr(module,type)
        bpy_factory.register_type(_type.bl_class,_type.bl_rep_class)