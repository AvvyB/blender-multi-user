import bpy
import mathutils

from .. import utils
from ..libs.replication.data import ReplicatedDatablock

class BlCurve(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        self.icon = 'CURVE_DATA'

        super().__init__( *args, **kwargs)

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

bl_id = "curves"
bl_class = bpy.types.Curve
bl_rep_class = BlCurve
bl_delay_refresh = 1
bl_delay_apply = 1
