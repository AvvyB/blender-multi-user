import bpy
import mathutils

from .. import utils
from ..libs.replication.data import ReplicatedDatablock

def load_gpencil_layer(target=None, data=None, create=False):

    utils.dump_anything.load(target, data)

    for frame in data["frames"]:
        try:
            tframe = target.frames[frame]
        except:
            tframe = target.frames.new(frame)
        utils.dump_anything.load(tframe, data["frames"][frame])
        for stroke in data["frames"][frame]["strokes"]:
            try:
                tstroke = tframe.strokes[stroke]
            except:
                tstroke = tframe.strokes.new()
            utils.dump_anything.load(
                tstroke, data["frames"][frame]["strokes"][stroke])

            for point in data["frames"][frame]["strokes"][stroke]["points"]:
                p = data["frames"][frame]["strokes"][stroke]["points"][point]

                tstroke.points.add(1)
                tpoint = tstroke.points[len(tstroke.points)-1]

                utils.dump_anything.load(tpoint, p)

class BlGpencil(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        self.icon = 'GREASEPENCIL'

        super().__init__( *args, **kwargs)
        
    def load(self, data, target):
        if target is None:
            target = bpy.data.grease_pencils.new(data["name"])

        for layer in target.layers:
            target.layers.remove(layer)

        if "layers" in data.keys():
            for layer in data["layers"]:
                if layer not in target.layers.keys():
                    gp_layer = target.layers.new(data["layers"][layer]["info"])
                else:
                    gp_layer = target.layers[layer]
                load_gpencil_layer(
                    target=gp_layer, data=data["layers"][layer], create=create)

        utils.dump_anything.load(target, data)

        target.materials.clear()
        if "materials" in data.keys():
            for mat in data['materials']:
                target.materials.append(bpy.data.materials[mat])



    def dump(self, pointer=None):
        assert(pointer)
        data = utils.dump_datablock(pointer, 2)
        utils.dump_datablock_attibutes(
            pointer, ['layers'], 9, data)
        return data

bl_id = "grease_pencils"
bl_class = bpy.types.GreasePencil
bl_rep_class = BlGpencil

