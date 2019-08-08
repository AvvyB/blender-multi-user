import bpy
import mathutils

from .. import utils
from ..libs.replication.data import ReplicatedDatablock

class BlObject(ReplicatedDatablock):
    def load(self, data, target):
        if target is None:
            pointer = None
            
            # Object specific constructor...
            if data["data"] in bpy.data.meshes.keys():
                pointer = bpy.data.meshes[data["data"]]
            elif data["data"] in bpy.data.lights.keys():
                pointer = bpy.data.lights[data["data"]]
            elif data["data"] in bpy.data.cameras.keys():
                pointer = bpy.data.cameras[data["data"]]
            elif data["data"] in bpy.data.curves.keys():
                pointer = bpy.data.curves[data["data"]]
            elif data["data"] in bpy.data.armatures.keys():
                pointer = bpy.data.armatures[data["data"]]
            elif data["data"] in bpy.data.grease_pencils.keys():
                pointer = bpy.data.grease_pencils[data["data"]]
            elif data["data"] in bpy.data.curves.keys():
                pointer = bpy.data.curves[data["data"]]

            target = bpy.data.objects.new(data["name"], pointer)

            # Load other meshes metadata

        target.matrix_world = mathutils.Matrix(data["matrix_world"])

    def dump(self, source):
        return utils.dump_datablock(source, 1)


bl_id = "objects"
bl_class = bpy.types.Object
bl_rep_class = BlObject 

