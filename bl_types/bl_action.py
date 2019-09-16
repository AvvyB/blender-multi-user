import bpy
import mathutils
from jsondiff import diff

from .. import utils
from .bl_datablock import BlDatablock

class BlAction(BlDatablock):
    def load(self, data, target):
        utils.dump_anything.load(target, data)

    def construct(self, data):
        return bpy.data.actions.new(data["name"])

    def dump(self, pointer=None):
        assert(pointer)
        data =  utils.dump_datablock(pointer, 1)

        dumper = utils.dump_anything.Dumper()
        dumper.depth = 2


        data["fcurves"] = []
        for fcurve in self.pointer.fcurves:
            fc = {
                "data_path": fcurve.data_path,
                "dumped_array_index": fcurve.array_index,
                "keyframe_points": []
            }

            for k in fcurve.keyframe_points:
                fc["keyframe_points"].append(
                    dumper.dump(k)
                )

            data["fcurves"].append(fc)

        return data
    
    def resolve(self):
        assert(self.buffer)      
        self.pointer = bpy.data.actions.get(self.buffer['name'])
    
    def diff(self):
        return False

bl_id = "actions"
bl_class = bpy.types.Action
bl_rep_class = BlAction
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'ACTION_DATA'