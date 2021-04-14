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

from .dump_anything import Loader, Dumper
from .bl_datablock import BlDatablock


class BlLibrary(BlDatablock):
    bl_id = "libraries"
    bl_class = bpy.types.Library
    bl_check_common = False
    bl_icon = 'LIBRARY_DATA_DIRECT'
    bl_reload_parent = False

    def _construct(self, data):
        with bpy.data.libraries.load(filepath=data["filepath"], link=True) as (sourceData, targetData):
            targetData = sourceData
            return sourceData
    def _load(self, data, target):
        pass

    def _dump(self, instance=None):
        assert(instance)
        dumper = Dumper()
        return dumper.dump(instance)


