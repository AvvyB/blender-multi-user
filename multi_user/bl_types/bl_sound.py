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


import logging
import os
from pathlib import Path

import bpy

from .bl_file import get_filepath, ensure_unpacked
from .bl_datablock import BlDatablock
from .dump_anything import Dumper, Loader


class BlSound(BlDatablock):
    bl_id = "sounds"
    bl_class = bpy.types.Sound
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = False
    bl_icon = 'SOUND'

    def _construct(self, data):
        filename = data.get('filename')

        return bpy.data.sounds.load(get_filepath(filename))

    def _load(self, data, target):
        loader = Loader()
        loader.load(target, data)

    def diff(self):
        return False

    def _dump(self, instance=None):
        filename = Path(instance.filepath).name

        if not filename:
            raise FileExistsError(instance.filepath)
 
        return {
            'filename': filename,
            'name': instance.name
        }

    def _resolve_deps_implementation(self):
        deps = []
        if self.instance.filepath and self.instance.filepath != '<builtin>':
            ensure_unpacked(self.instance)
            
            deps.append(Path(bpy.path.abspath(self.instance.filepath)))

        return deps
