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
import pathlib
from .. import utils
from .dump_anything import Loader, Dumper
from .bl_datablock import BlDatablock

class BlSound(BlDatablock):
    bl_id = "sounds"
    bl_class = bpy.types.Sound
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = False
    bl_icon = 'SOUND'

    def _construct(self, data):
        if 'file' in data.keys():
            prefs = utils.get_preferences()
            ext = data['filepath'].split(".")[-1]
            sound_name = f"{self.uuid}.{ext}"
            sound_path = os.path.join(prefs.cache_directory, sound_name)
            
            os.makedirs(prefs.cache_directory, exist_ok=True)
            file = open(sound_path, 'wb')
            file.write(data["file"])
            file.close()

            logging.info(f'loading {sound_path}')
            return bpy.data.sounds.load(sound_path)

    def _load(self, data, target):
        loader = Loader()
        loader.load(target, data)

    def _dump(self, instance=None):
        if not instance.packed_file:
            # prefs = utils.get_preferences()
            # ext = pathlib.Path(instance.filepath).suffix
            # sound_name = f"{self.uuid}{ext}"
            # sound_path = os.path.join(prefs.cache_directory, sound_name)
            # instance.filepath = sound_path
            instance.pack()
            #TODO:use file locally with unpack(method='USE_ORIGINAL') ?

        return {
            'filepath':instance.filepath,
            'name':instance.name,
            'file': instance.packed_file.data
        }


    def diff(self):
        return False
