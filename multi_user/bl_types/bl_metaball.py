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

from .dump_anything import (
    Dumper, Loader, np_dump_collection_primitive, np_load_collection_primitives,
    np_dump_collection, np_load_collection)

from replication.protocol import ReplicatedDatablock


ELEMENT = [
    'co',
    'hide',
    'radius',
    'rotation',
    'size_x',
    'size_y',
    'size_z',
    'stiffness',
    'type'
]


def dump_metaball_elements(elements):
    """ Dump a metaball element

        :arg element: metaball element
        :type bpy.types.MetaElement
        :return: dict
    """

    dumped_elements = np_dump_collection(elements, ELEMENT)

    return dumped_elements


def load_metaball_elements(elements_data, elements):
    """ Dump a metaball element

        :arg element: metaball element
        :type bpy.types.MetaElement
        :return: dict
    """
    np_load_collection(elements_data, elements, ELEMENT)


class BlMetaball(ReplicatedDatablock):
    bl_id = "metaballs"
    bl_class = bpy.types.MetaBall
    bl_check_common = False
    bl_icon = 'META_BALL'
    bl_reload_parent = False

    def construct(data: dict) -> object:
        return bpy.data.metaballs.new(data["name"])

    def load(data: dict, datablock: object):
        loader = Loader()
        loader.load(target, data)

        target.elements.clear()

        for mtype in data["elements"]['type']:
            new_element = target.elements.new()

        load_metaball_elements(data['elements'], target.elements)

    def dump(datablock: object) -> dict:
        assert(instance)
        dumper = Dumper()
        dumper.depth = 1
        dumper.include_filter = [
            'name',
            'resolution',
            'render_resolution',
            'threshold',
            'update_method',
            'use_auto_texspace',
            'texspace_location',
            'texspace_size'
        ]

        data = dumper.dump(instance)
        data['elements'] = dump_metaball_elements(instance.elements)

        return data
