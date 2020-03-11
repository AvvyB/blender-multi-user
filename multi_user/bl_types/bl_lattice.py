import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock


class BlLattice(BlDatablock):
    bl_id = "lattices"
    bl_class = bpy.types.Lattice
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'LATTICE_DATA'

    def load_implementation(self, data, target):
        utils.dump_anything.load(target, data)

        for point in data['points']:
            utils.dump_anything.load(target.points[point], data["points"][point])
    def construct(self, data):
        return bpy.data.lattices.new(data["name"])

    def dump_implementation(self, data, pointer=None):
        assert(pointer)

        dumper = utils.dump_anything.Dumper()
        dumper.depth = 3
        dumper.include_filter = [
            "name",
            'type',
            'points_u',
            'points_v',
            'points_w',
            'interpolation_type_u',
            'interpolation_type_v',
            'interpolation_type_w',
            'use_outside',
            'points',
            'co',
            'weight_softbody',
            'co_deform'
        ]
        data = dumper.dump(pointer)

        return data





