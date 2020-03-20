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

from .. import utils
from .bl_datablock import BlDatablock


class BlMetaball(BlDatablock):
    bl_id = "metaballs"
    bl_class = bpy.types.MetaBall
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'META_BALL'

    def _construct(self, data):
        return bpy.data.metaballs.new(data["name"])

    def load(self, data, target):
        utils.dump_anything.load(target, data)
        
        target.elements.clear()
        for element in data["elements"]:
            new_element = target.elements.new(type=data["elements"][element]['type'])
            utils.dump_anything.load(new_element, data["elements"][element])

    def dump_implementation(self, data, pointer=None):
        assert(pointer)
        dumper = utils.dump_anything.Dumper()
        dumper.depth = 3
        dumper.exclude_filter = ["is_editmode"]

        data = dumper.dump(pointer)
        return data



