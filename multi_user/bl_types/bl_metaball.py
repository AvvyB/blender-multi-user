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

from .. import utils
from ..libs.dump_anything import (
    Dumper, Loader, dump_collection_attr, load_collection_attr, dump_collection_attr_to_dict, load_collection_attr_from_dict)

from .bl_datablock import BlDatablock

ENUM_METABALL_TYPE = [
    'BALL',
    'CAPSULE',
    'PLANE',
    'ELLIPSOID',
    'CUBE'
]


ELEMENTS_FAST_ATTR = [
        'co',
        'hide',
        'radius',
        'rotation',
        'size_x',
        'size_y',
        'size_z',
        'stiffness']


def dump_metaball_elements(elements):
    """ Dump a metaball element

        :arg element: metaball element
        :type bpy.types.MetaElement
        :return: dict
    """
    
    dumped_elements = {}

    dump_collection_attr_to_dict(dumped_elements, elements, ELEMENTS_FAST_ATTR)
    
    dumped_elements['type'] = [ENUM_METABALL_TYPE.index(e.type) for e in elements]

    return dumped_elements


def load_metaball_elements(elements_data, elements):
    """ Dump a metaball element

        :arg element: metaball element
        :type bpy.types.MetaElement
        :return: dict
    """
    load_collection_attr_from_dict(elements_data, elements, ELEMENTS_FAST_ATTR)


class BlMetaball(BlDatablock):
    bl_id = "metaballs"
    bl_class = bpy.types.MetaBall
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'META_BALL'

    def _construct(self, data):
        return bpy.data.metaballs.new(data["name"])

    def _load_implementation(self, data, target):
        utils.dump_anything.load(target, data)

        target.elements.clear()

        for element_type in data["elements"]['type']:
            new_element = target.elements.new(
                type=ENUM_METABALL_TYPE[element_type])
        
        load_metaball_elements(data['elements'], target.elements)

    def _dump_implementation(self, data, pointer=None):
        assert(pointer)
        dumper = utils.dump_anything.Dumper()
        dumper.depth = 1
        dumper.exclude_filter = [
            "is_editmode",
            "is_evaluated",
            "is_embedded_data",
            "is_library_indirect",
            "name_full"
        ]

        data = dumper.dump(pointer)
        data['elements'] = dump_metaball_elements(pointer.elements)

        return data

