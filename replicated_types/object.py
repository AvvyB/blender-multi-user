from libs.replication.data import ReplicatedDatablock
import bpy
import mathutils

class RepObject(ReplicatedDatablock):
    def load(self, data, target):
        try:
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
    
            target.id = data['id']
    
            client = bpy.context.window_manager.session.username
    
            if target.id == client or target.id == "Common":
                target.hide_select = False
            else:
                target.hide_select = True
        
        except Exception as e:
            logger.error("Object {} loading error: {} ".format(data["name"], e))
