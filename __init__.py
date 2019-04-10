bl_info = {
    "name" : "rcf",
    "author" : "CUBE",
    "description" : "",
    "blender" : (2, 80, 0),
    "location" : "",
    "warning" : "",
    "category" : "Collaboration"
}


import bpy
import os
import sys


from . import operators
from . import ui

def register():
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()

    