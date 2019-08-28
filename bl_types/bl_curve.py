import bpy
import mathutils
from jsondiff import diff

from .. import utils
from .bl_datablock import BlDatablock

class BlCurve(BlDatablock):
    def construct(self, data):
        return bpy.data.curves.new(data["name"], 'CURVE')

    def load(self, data, target):
        utils.dump_anything.load(target, data)

        target.splines.clear()
        # load splines
        for spline in data['splines']:
            # Update existing..
            # if spline in target.splines.keys():

            new_spline = target.splines.new(data['splines'][spline]['type'])
            utils.dump_anything.load(new_spline, data['splines'][spline])

            # Load curve geometry data
            for bezier_point_index in data['splines'][spline]["bezier_points"]:
                new_spline.bezier_points.add(1)
                utils.dump_anything.load(
                    new_spline.bezier_points[bezier_point_index], data['splines'][spline]["bezier_points"][bezier_point_index])

            for point_index in data['splines'][spline]["points"]:
                new_spline.points.add(1)
                utils.dump_anything.load(
                    new_spline.points[point_index], data['splines'][spline]["points"][point_index])

    def dump(self, pointer=None):
        assert(pointer)
        data = utils.dump_datablock(pointer, 1)
        utils.dump_datablock_attibutes(
            pointer, ['splines'], 5, data)
        return data

    def resolve(self):
        assert(self.buffer)      
        self.pointer = bpy.data.curves.get(self.buffer['name'])

    def diff(self):
        return (self.bl_diff() or
                len(diff(self.dump(pointer=self.pointer), self.buffer)) > 1)

bl_id = "curves"
bl_class = bpy.types.Curve
bl_rep_class = BlCurve
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'CURVE_DATA'