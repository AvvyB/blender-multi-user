import bpy
import mathutils

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
            new_spline = target.splines.new(data['splines'][spline]['type'])
            utils.dump_anything.load(new_spline, data['splines'][spline])

            # Load curve geometry data
            for bezier_point_index in data['splines'][spline]["bezier_points"]:
                if bezier_point_index != 0:
                    new_spline.bezier_points.add(1)
                utils.dump_anything.load(
                    new_spline.bezier_points[bezier_point_index], data['splines'][spline]["bezier_points"][bezier_point_index])

            for point_index in data['splines'][spline]["points"]:
                new_spline.points.add(1)
                utils.dump_anything.load(
                    new_spline.points[point_index], data['splines'][spline]["points"][point_index])

    def dump_implementation(self, data, pointer=None):
        assert(pointer)
        data = utils.dump_datablock(pointer, 1)
        data['splines'] = {}

        dumper = utils.dump_anything.Dumper()
        dumper.depth = 3
        
        for index,spline in enumerate(pointer.splines):
            spline_data = {}
            spline_data['points'] = dumper.dump(spline.points)
            spline_data['bezier_points'] = dumper.dump(spline.bezier_points)
            spline_data['type'] = dumper.dump(spline.type)
            data['splines'][index] = spline_data

        if isinstance(pointer,'TextCurve'):
            data['type'] = 'TEXT'
        if isinstance(pointer,'SurfaceCurve'):
            data['type'] = 'SURFACE'
        if isinstance(pointer,'TextCurve'):
            data['type'] = 'CURVE'
        return data

    def resolve(self):
        self.pointer = utils.find_from_attr('uuid', self.uuid, bpy.data.curves)

    def is_valid(self):
        return bpy.data.curves.get(self.data['name'])
bl_id = "curves"
bl_class = bpy.types.Curve
bl_rep_class = BlCurve
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'CURVE_DATA'