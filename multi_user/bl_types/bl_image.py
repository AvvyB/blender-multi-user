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
from .bl_datablock import BlDatablock
from .dump_anything import Dumper, Loader
from .bl_file import get_filepath

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


class BlImage(BlDatablock):
    bl_id = "images"
    bl_class = bpy.types.Image
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = False
    bl_icon = 'IMAGE_DATA'

    def _construct(self, data):
        return bpy.data.images.new(
            name=data['name'],
            width=data['size'][0],
            height=data['size'][1]
        )

    def _load(self, data, target):
        target.source = 'FILE'
        target.filepath_raw = get_filepath(data['filename'])
        target.colorspace_settings.name = data["colorspace_settings"]["name"]

        loader = Loader()
        loader.load(data, target)

    def _dump(self, instance=None):
        assert(instance)

        filename = Path(instance.filepath).name

        # Cache the image on the disk
        if instance.source == "GENERATED" or instance.packed_file is not None:
            instance.filepath = get_filepath(filename)
            instance.save()

        data = {
            "filename": filename
        }

        dumper = Dumper()
        dumper.depth = 2
        dumper.include_filter = [
            "name",
            'size',
            'height',
            'alpha',
            'float_buffer',
            'alpha_mode',
            'colorspace_settings']
        data.update(dumper.dump(instance))
        return data

    def diff(self):
        if self.instance and (self.instance.name != self.data['name']):
            return True
        else:
            return False

    def _resolve_deps_implementation(self):
        deps = []
        if self.instance.filepath:
            deps.append(Path(self.instance.filepath))

        return deps
