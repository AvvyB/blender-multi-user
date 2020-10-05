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

from .bl_datablock import BlDatablock
from .bl_file import get_filepath, ensure_unpacked
from .dump_anything import Dumper, Loader


class BlFont(BlDatablock):
    bl_id = "fonts"
    bl_class = bpy.types.VectorFont
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = False
    bl_icon = 'FILE_FONT'

    def _construct(self, data):
        filename = data.get('filename')

        if filename == '<builtin>':
            return bpy.data.fonts.load(filename)
        else:
            return bpy.data.fonts.load(get_filepath(filename))

    def _load(self, data, target):
        pass

    def _dump(self, instance=None):
        if instance.filepath  == '<builtin>':
            filename = '<builtin>'
        else:
            filename = Path(instance.filepath).name

        if not filename:
            raise FileExistsError(instance.filepath)

        return {
            'filename': filename,
            'name': instance.name
        }

    def diff(self):
        return False

    def _resolve_deps_implementation(self):
        deps = []
        if self.instance.filepath and self.instance.filepath != '<builtin>':
            ensure_unpacked(self.instance)

            deps.append(Path(bpy.path.abspath(self.instance.filepath)))

        return deps
