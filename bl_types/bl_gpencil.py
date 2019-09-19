import bpy
import mathutils
from jsondiff import diff

from .. import utils
from .bl_datablock import BlDatablock


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


class BlGpencil(BlDatablock):
    def construct(self, data):
        return bpy.data.grease_pencils.new(data["name"])

    def load(self, data, target):
        for layer in target.layers:
            target.layers.remove(layer)

        if "layers" in data.keys():
            for layer in data["layers"]:
                if layer not in target.layers.keys():
                    gp_layer = target.layers.new(data["layers"][layer]["info"])
                else:
                    gp_layer = target.layers[layer]
                load_gpencil_layer(
                    target=gp_layer, data=data["layers"][layer], create=True)

        utils.dump_anything.load(target, data)

        target.materials.clear()
        if "materials" in data.keys():
            for mat in data['materials']:
                target.materials.append(bpy.data.materials[mat])

    def diff(self):
        return (self.bl_diff() or
                len(diff(self.dump(pointer=self.pointer), self.buffer)) > 0)

    def dump(self, pointer=None):
        assert(pointer)
        data = utils.dump_datablock(pointer, 2)
        utils.dump_datablock_attibutes(
            pointer, ['layers'], 9, data)
        return data

    def resolve(self):
        assert(self.buffer)
        self.pointer = bpy.data.grease_pencils.get(self.buffer['name'])

    def resolve_dependencies(self):
        deps = []

        for material in self.pointer.materials:
            deps.append(material)

        return deps


bl_id = "grease_pencils"
bl_class = bpy.types.GreasePencil
bl_rep_class = BlGpencil
bl_delay_refresh = 5
bl_delay_apply = 5
bl_automatic_push = True
bl_icon = 'GREASEPENCIL'