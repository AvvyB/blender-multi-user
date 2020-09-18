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
import os
import logging
from .. import utils
from .dump_anything import Loader, Dumper
from .bl_datablock import BlDatablock

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

    def dump_image(self, image):
        pixels = None
        if image.source == "GENERATED" or image.packed_file is not None:
            prefs = utils.get_preferences()
            img_name = f"{self.uuid}.{format_to_ext[image.file_format]}"

            # Cache the image on the disk
            image.filepath_raw = os.path.join(prefs.cache_directory, img_name)
            os.makedirs(prefs.cache_directory, exist_ok=True)
            image.save()

        if image.source == "FILE":
            image_path = bpy.path.abspath(image.filepath_raw)
            image_directory = os.path.dirname(image_path)
            os.makedirs(image_directory, exist_ok=True)
            image.save()
            file = open(image_path, "rb")
            pixels = file.read()
            file.close()
        else:
            raise ValueError()
        return pixels

    def _construct(self, data):
        return bpy.data.images.new(
            name=data['name'],
            width=data['size'][0],
            height=data['size'][1]
        )

    def _load(self, data, target):
        image = target
        prefs = utils.get_preferences()
        img_format = data['file_format']
        img_name = f"{self.uuid}.{format_to_ext[img_format]}"

        img_path = os.path.join(prefs.cache_directory, img_name)
        os.makedirs(prefs.cache_directory, exist_ok=True)
        file = open(img_path, 'wb')
        file.write(data["pixels"])
        file.close()

        image.source = 'FILE'
        image.filepath = img_path
        image.colorspace_settings.name = data["colorspace_settings"]["name"]
        # Unload image from memory
        del data['pixels']

        loader = Loader()
        loader.load(data, target)

    def _dump(self, instance=None):
        assert(instance)
        data = {}
        data['pixels'] = self.dump_image(instance)
        dumper = Dumper()
        dumper.depth = 2
        dumper.include_filter = [
            "name",
            'size',
            'height',
            'alpha',
            'float_buffer',
            'file_format',
            'alpha_mode',
            'filepath',
            'source',
            'colorspace_settings']
        data.update(dumper.dump(instance))

        return data

    def diff(self):
        if self.instance and (self.instance.name != self.data['name']):
            return True
        else:
            return False
