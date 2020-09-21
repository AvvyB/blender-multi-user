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
import sys
from pathlib import Path

import bpy
import mathutils
from replication.constants import DIFF_BINARY, UP
from replication.data import ReplicatedDatablock

from .. import utils
from .dump_anything import Dumper, Loader


def get_filepath(filename):
    """
    Construct the local filepath 
    """
    return str(Path(
        utils.get_preferences().cache_directory,
        filename
    ))


def ensure_unpacked(datablock):
    if datablock.packed_file:
        logging.info(f"Unpacking {datablock.name}")

        filename = Path(bpy.path.abspath(datablock.filepath)).name
        datablock.filepath = get_filepath(filename)

        datablock.unpack(method="WRITE_ORIGINAL")


class BlFile(ReplicatedDatablock):
    bl_id = 'file'
    bl_name = "file"
    bl_class = Path
    bl_delay_refresh = 0
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = False
    bl_icon = 'FILE'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = kwargs.get('instance', None)
        self.preferences = utils.get_preferences()
        self.diff_method = DIFF_BINARY

    def resolve(self):
        if self.data:
            self.instance = Path(get_filepath(self.data['name']))

    def push(self, socket, identity=None):
        super().push(socket, identity=None)
        
        if self.preferences.clear_memory_filecache:
                del self.data['file']

    def _dump(self, instance=None):
        """
        Read the file and return a dict as:
        {
            name : filename
            extension :
            file: file content
        }
        """
        logging.info(f"Extracting file metadata")

        data = {
            'name': self.instance.name,
        }

        logging.info(
            f"Reading {self.instance.name} content: {self.instance.stat().st_size} bytes")

        try:
            file = open(self.instance, "rb")
            data['file'] = file.read()

            file.close()
        except IOError:
            logging.warning(f"{self.instance} doesn't exist, skipping")
        else:
            file.close()

        return data

    def _load(self, data, target):
        """
        Writing the file
        """
        # TODO: check for empty data

        if target.exists() and not self.diff():
            logging.info(f"{data['name']} already on the disk, skipping.")
            return
        try:
            file = open(target, "wb")
            file.write(data['file'])
            
            if self.preferences.clear_memory_filecache:
                del self.data['file']
        except IOError:
            logging.warning(f"{target} doesn't exist, skipping")
        else:
            file.close()

    def diff(self):
        memory_size = sys.getsizeof(self.data['file'])-33
        disk_size = self.instance.stat().st_size
        return memory_size == disk_size
