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
import mathutils

from .. import utils
from replication.protocol import ReplicatedDatablock
from .dump_anything import Dumper, Loader
from .bl_file import get_filepath, ensure_unpacked

format_to_ext = {
    'BMP': 'bmp',
    'IRIS': 'sgi',
    'PNG': 'png',
    'JPEG': 'jpg',
    'JPEG2000': 'jp2',
    'TARGA': 'tga',
    'TARGA_RAW': 'tga',
    'CINEON': 'cin',
    'DPX': 'dpx',
    'OPEN_EXR_MULTILAYER': 'exr',
    'OPEN_EXR': 'exr',
    'HDR': 'hdr',
    'TIFF': 'tiff',
    'AVI_JPEG': 'avi',
    'AVI_RAW': 'avi',
    'FFMPEG': 'mpeg',
}


class BlImage(ReplicatedDatablock):
    bl_id = "images"
    bl_class = bpy.types.Image
    bl_check_common = False
    bl_icon = 'IMAGE_DATA'
    bl_reload_parent = False

    def construct(data: dict) -> object:
        return bpy.data.images.new(
            name=data['name'],
            width=data['size'][0],
            height=data['size'][1]
        )

    def _load(self, data, target):
        loader = Loader()
        loader.load(data, target)

        target.source = 'FILE'
        target.filepath_raw = get_filepath(data['filename'])
        color_space_name = data["colorspace_settings"]["name"]

        if color_space_name:
            target.colorspace_settings.name = color_space_name

    def _dump(self, instance=None):
        assert(instance)

        filename = Path(instance.filepath).name

        data = {
            "filename": filename
        }

        dumper = Dumper()
        dumper.depth = 2
        dumper.include_filter = [
            "name",
            # 'source',
            'size',
            'height',
            'alpha',
            'float_buffer',
            'alpha_mode',
            'colorspace_settings']
        data.update(dumper.dump(instance))
        return data

    def diff(self):
        if self.instance.is_dirty:
            self.instance.save()
        
        if not self.data or (self.instance and (self.instance.name != self.data['name'])):
            return super().diff()
        else:
            return None

    def resolve_deps(datablock: object) -> [object]:
        deps = []

        if self.instance.packed_file:
            filename = Path(bpy.path.abspath(self.instance.filepath)).name
            self.instance.filepath_raw = get_filepath(filename)
            self.instance.save()
            # An image can't be unpacked to the modified path
            # TODO: make a bug report
            self.instance.unpack(method="REMOVE")

        elif self.instance.source == "GENERATED":
            filename = f"{self.instance.name}.png"
            self.instance.filepath = get_filepath(filename)
            self.instance.save()

        if self.instance.filepath:
            deps.append(Path(bpy.path.abspath(self.instance.filepath)))

        return deps
