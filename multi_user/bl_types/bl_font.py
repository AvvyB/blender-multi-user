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

from replication.protocol import ReplicatedDatablock
from .bl_file import get_filepath, ensure_unpacked
from .dump_anything import Dumper, Loader
from .bl_datablock import resolve_datablock_from_uuid

class BlFont(ReplicatedDatablock):
    bl_id = "fonts"
    bl_class = bpy.types.VectorFont
    bl_check_common = False
    bl_icon = 'FILE_FONT'
    bl_reload_parent = False

    @staticmethod
    def construct(data: dict) -> object:
        filename = data.get('filename')

        if filename == '<builtin>':
            return bpy.data.fonts.load(filename)
        else:
            return bpy.data.fonts.load(get_filepath(filename))

    @staticmethod
    def load(data: dict, datablock: object):
        pass

    @staticmethod
    def dump(datablock: object) -> dict:
        if datablock.filepath  == '<builtin>':
            filename = '<builtin>'
        else:
            filename = Path(datablock.filepath).name

        if not filename:
            raise FileExistsError(datablock.filepath)

        return {
            'filename': filename,
            'name': datablock.name
        }

    def diff(self):
        return False

    @staticmethod
    def resolve(data: dict) -> object:
        uuid = data.get('uuid')
        name = data.get('name')
        datablock = resolve_datablock_from_uuid(uuid, bpy.data.fonts)
        if datablock is None:
            datablock = bpy.data.fonts.get(name)

        return datablock

    @staticmethod
    def resolve_deps(datablock: object) -> [object]:
        deps = []
        if datablock.filepath and datablock.filepath != '<builtin>':
            ensure_unpacked(datablock)

            deps.append(Path(bpy.path.abspath(datablock.filepath)))

        return deps

_type = bpy.types.VectorFont
_class = BlFont