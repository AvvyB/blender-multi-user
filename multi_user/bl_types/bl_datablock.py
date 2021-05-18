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
from collections.abc import Iterable

import bpy
import mathutils
from replication.constants import DIFF_BINARY, DIFF_JSON, UP
from replication.protocol import ReplicatedDatablock

from .. import utils
from .dump_anything import Dumper, Loader

def get_datablock_from_uuid(uuid, default, ignore=[]):
    if not uuid:
        return default
    for category in dir(bpy.data):
        root = getattr(bpy.data, category)
        if isinstance(root, Iterable) and category not in ignore:
            for item in root:
                if getattr(item, 'uuid', None) == uuid:
                    return item
    return default

def resolve_datablock_from_uuid(uuid, bpy_collection):
    for item in bpy_collection:
        if getattr(item, 'uuid', None) == uuid:
            return item
    return None

def resolve_from_root(data: dict, root: str, construct = True):
    datablock_root = getattr(bpy.data, self.bl_id)
    datablock_ref = utils.find_from_attr('uuid', self.uuid, datablock_root)

    if not datablock_ref:
        try:
            datablock_ref = datablock_root[self.data['name']]
        except Exception:
            pass

        if construct and not datablock_ref:
            name = self.data.get('name')
            logging.debug(f"Constructing {name}")
            datablock_ref = self._construct(data=self.data)

    if datablock_ref is not None:
        setattr(datablock_ref, 'uuid', self.uuid)
        self.instance = datablock_ref
        return True
    else:
        return False
