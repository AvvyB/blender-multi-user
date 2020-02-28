import bpy
import mathutils
import copy

from .. import utils
from .bl_datablock import BlDatablock

# WIP

class BlAction(BlDatablock):
    bl_id = "actions"
    bl_class = bpy.types.Action
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'ACTION_TWEAK'
    
    def construct(self, data):
        return bpy.data.actions.new(data["name"])

    def load(self, data, target):
        begin_frame = 100000
        end_frame = -100000

        for dumped_fcurve in data["fcurves"]:
            begin_frame = min(
                begin_frame,
                min(
                    [begin_frame] + [dkp["co"][0] for dkp in dumped_fcurve["keyframe_points"]]
                )
            )
            end_frame = max(
                end_frame,
                max(
                    [end_frame] + [dkp["co"][0] for dkp in dumped_fcurve["keyframe_points"]]
                )
            )
        begin_frame = 0

        loader = utils.dump_anything.Loader()
        for dumped_fcurve in data["fcurves"]:
            dumped_data_path = dumped_fcurve["data_path"]
            dumped_array_index = dumped_fcurve["dumped_array_index"]

            # create fcurve if needed
            fcurve = target.fcurves.find(dumped_data_path, index=dumped_array_index)
            if fcurve is None:
                fcurve = target.fcurves.new(dumped_data_path, index=dumped_array_index)


            # remove keyframes within dumped_action range
            for keyframe in reversed(fcurve.keyframe_points):
                if end_frame >= (keyframe.co[0] + begin_frame ) >= begin_frame:
                    fcurve.keyframe_points.remove(keyframe, fast=True)

            # paste dumped keyframes
            for dumped_keyframe_point in dumped_fcurve["keyframe_points"]:
                if dumped_keyframe_point['type'] == '':
                    dumped_keyframe_point['type'] = 'KEYFRAME' 

                new_kf = fcurve.keyframe_points.insert(
                    dumped_keyframe_point["co"][0] - begin_frame,
                    dumped_keyframe_point["co"][1],
                    options={'FAST', 'REPLACE'}
                )

                keycache  = copy.copy(dumped_keyframe_point)
                keycache =  utils.dump_anything.remove_items_from_dict(
                        keycache,
                        ["co", "handle_left", "handle_right",'type']
                    )
                
                loader.load(
                    new_kf,
                    keycache
                )

                new_kf.type = dumped_keyframe_point['type']
                new_kf.handle_left = [
                    dumped_keyframe_point["handle_left"][0] - begin_frame,
                    dumped_keyframe_point["handle_left"][1]
                ]
                new_kf.handle_right = [
                    dumped_keyframe_point["handle_right"][0] - begin_frame,
                    dumped_keyframe_point["handle_right"][1]
                ]

            # clearing (needed for blender to update well)
            if len(fcurve.keyframe_points) == 0:
                target.fcurves.remove(fcurve)
        target.id_root= data['id_root']

    def dump(self, pointer=None):
        assert(pointer)
        dumper = utils.dump_anything.Dumper()
        dumper.exclude_filter =[
            'name_full',
            'original',
            'use_fake_user',
            'user',
            'is_library_indirect',
            'select_control_point',
            'select_right_handle',
            'select_left_handle',
            'uuid',
            'users'
        ]
        dumper.depth = 1
        data =  dumper.dump(pointer)

        
        data["fcurves"] = []
        dumper.depth = 2
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

    def is_valid(self):
        return bpy.data.actions.get(self.data['name'])


