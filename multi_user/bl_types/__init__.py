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


__all__ = [
    'bl_object',
    'bl_mesh',
    'bl_camera',
    'bl_collection',
    'bl_curve',
    'bl_gpencil',
    'bl_image',
    'bl_light',
    'bl_scene',
    'bl_material',
    'bl_library',
    'bl_armature',
    'bl_action',
    'bl_world',
    'bl_metaball',
    'bl_lattice',
    'bl_lightprobe',
    'bl_speaker',
    'bl_font',
    'bl_sound',
    'bl_file',
    'bl_sequencer',
    'bl_node_group',
    'bl_texture'
]  # Order here defines execution order

from . import *
from replication.data import ReplicatedDataFactory

def types_to_register():
    return __all__

