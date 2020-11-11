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

from .dump_anything import Dumper, Loader, np_dump_collection, np_load_collection
from .bl_datablock import BlDatablock
from .bl_material import (dump_shader_node_tree,
                          load_shader_node_tree,
                          get_node_tree_dependencies)

class BlNodeGroup(BlDatablock):
    bl_id = "node_groups"
    bl_class = bpy.types.ShaderNodeTree
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = False
    bl_icon = 'NODETREE'

    def _construct(self, data):
        return bpy.data.node_groups.new(data["name"], data["type"])

    def _load_implementation(self, data, target):
        load_shader_node_tree(data, target)

    def _dump_implementation(self, data, instance=None):
        return dump_shader_node_tree(instance)

    def _resolve_deps_implementation(self):
        return get_node_tree_dependencies(self.instance)