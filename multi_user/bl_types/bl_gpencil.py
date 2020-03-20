# ##### BEGIN GPL LICENSE BLOCK #####
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


import bpy
import mathutils

from ..libs import dump_anything 
from .bl_datablock import BlDatablock


def load_gpencil_layer(target=None, data=None, create=False):

    dump_anything.load(target, data)
    for k,v in target.frames.items():
        target.frames.remove(v)
        
    for frame in data["frames"]:
        
        tframe = target.frames.new(data["frames"][frame]['frame_number'])

        for stroke in data["frames"][frame]["strokes"]:
            try:
                tstroke = tframe.strokes[stroke]
            except:
                tstroke = tframe.strokes.new()
            dump_anything.load(
                tstroke, data["frames"][frame]["strokes"][stroke])

            for point in data["frames"][frame]["strokes"][stroke]["points"]:
                p = data["frames"][frame]["strokes"][stroke]["points"][point]

                tstroke.points.add(1)
                tpoint = tstroke.points[len(tstroke.points)-1]

                dump_anything.load(tpoint, p)


class BlGpencil(BlDatablock):
    bl_id = "grease_pencils"
    bl_class = bpy.types.GreasePencil
    bl_delay_refresh = 5
    bl_delay_apply = 5
    bl_automatic_push = True
    bl_icon = 'GREASEPENCIL'

    def _construct(self, data):
        return bpy.data.grease_pencils.new(data["name"])

    def load_implementation(self, data, target):
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

        dump_anything.load(target, data)

        target.materials.clear()
        if "materials" in data.keys():
            for mat in data['materials']:
                target.materials.append(bpy.data.materials[mat])

    def dump_implementation(self, data, pointer=None):
        assert(pointer)
        data = dump_anything.dump(pointer, 2)
        data['layers'] = dump_anything.dump(pointer.layers, 9)

        return data

    def resolve_deps_implementation(self):
        deps = []

        for material in self.pointer.materials:
            deps.append(material)

        return deps
