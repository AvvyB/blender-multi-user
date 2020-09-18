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

class BlFont(BlDatablock):
    bl_id = "fonts"
    bl_class = bpy.types.VectorFont
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = False
    bl_icon = 'FILE_FONT'

    def _construct(self, data):
        if data['filepath'] == '<builtin>':
            return bpy.data.fonts.load(data['filepath'])
        elif 'font_file' in data.keys():
            prefs = utils.get_preferences()
            font_name = f"{self.uuid}.ttf"
            font_path = os.path.join(prefs.cache_directory, font_name)
            
            os.makedirs(prefs.cache_directory, exist_ok=True)
            file = open(font_path, 'wb')
            file.write(data["font_file"])
            file.close()

            logging.info(f'loading {font_path}')
            return bpy.data.fonts.load(font_path)

        return bpy.data.images.new(
            name=data['name'],
            width=data['size'][0],
            height=data['size'][1]
        )

    def _load(self, data, target):
        pass

    def _dump(self, instance=None):
        data = {
            'filepath':instance.filepath,
            'name':instance.name
        }
        if instance.filepath != '<builtin>' and not instance.is_embedded_data:            
            file = open(instance.filepath, "rb")
            data['font_file'] = file.read()
            file.close()
        return data

    def diff(self):
        return False
