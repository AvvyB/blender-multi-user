bl_info = {
    "name" : "rcf",
    "author" : "CUBE",
    "description" : "",
    "blender" : (2, 80, 0),
    "location" : "",
    "warning" : "",
    "category" : "Collaboration"
}

from .libs.bsyncio import bsyncio


import bpy
import os
import sys


from . import net_operators
from . import net_ui
from . import net_ecs

def register():
    bsyncio.register()
    net_operators.register()
    net_ui.register()
    net_ecs.register()

def unregister():
    bsyncio.unregister()
    net_ui.unregister()
    net_operators.unregister()
    net_ecs.unregister()