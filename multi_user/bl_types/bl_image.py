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

def dump_image(image):
    pixels = None
    if image.source == "GENERATED" or image.packed_file is not None:
        prefs = utils.get_preferences()
        img_name = f"{image.name}.png"
        
        # Cache the image on the disk
        image.filepath_raw = os.path.join(prefs.cache_directory, img_name)
        os.makedirs(prefs.cache_directory, exist_ok=True)
        image.file_format = "PNG"
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

class BlImage(BlDatablock):
    bl_id = "images"
    bl_class = bpy.types.Image
    bl_delay_refresh = 0
    bl_delay_apply = 1
    bl_automatic_push = False
    bl_check_common = False
    bl_icon = 'IMAGE_DATA'

    def _construct(self, data):
        return bpy.data.images.new(
                name=data['name'],
                width=data['size'][0],
                height=data['size'][1]
            )

    def _load(self, data, target):
        image = target
        prefs = utils.get_preferences()

        img_name = f"{image.name}.png"

        img_path = os.path.join(prefs.cache_directory,img_name)
        os.makedirs(prefs.cache_directory, exist_ok=True)
        file = open(img_path, 'wb')
        file.write(data["pixels"])
        file.close()

        image.source = 'FILE'
        image.filepath = img_path
        image.colorspace_settings.name = data["colorspace_settings"]["name"]


    def _dump(self, instance=None):
        assert(instance)
        data = {}
        data['pixels'] = dump_image(instance)
        dumper = Dumper()
        dumper.depth = 2
        dumper.include_filter = [   
                "name",
                'size',
                'height',
                'alpha',
                'float_buffer',
                'filepath',
                'source',
                'colorspace_settings']
        data.update(dumper.dump(instance))

        return data

    def diff(self):
        return False
    

