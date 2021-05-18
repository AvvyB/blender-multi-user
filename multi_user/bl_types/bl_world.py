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

from .dump_anything import Loader, Dumper
from replication.protocol import ReplicatedDatablock
from .bl_material import (load_node_tree,
                          dump_node_tree,
                          get_node_tree_dependencies)


class BlWorld(ReplicatedDatablock):
    bl_id = "worlds"
    bl_class = bpy.types.World
    bl_check_common = True
    bl_icon = 'WORLD_DATA'
    bl_reload_parent = False

    def construct(data: dict) -> object:
        return bpy.data.worlds.new(data["name"])

    def load(data: dict, datablock: object):
        loader = Loader()
        loader.load(target, data)

        if data["use_nodes"]:
            if target.node_tree is None:
                target.use_nodes = True

            load_node_tree(data['node_tree'], target.node_tree)

    def dump(datablock: object) -> dict:
        assert(instance)

        world_dumper = Dumper()
        world_dumper.depth = 1
        world_dumper.include_filter = [
            "use_nodes",
            "name",
            "color"
        ]
        data = world_dumper.dump(instance)
        if instance.use_nodes:
            data['node_tree'] = dump_node_tree(instance.node_tree)

        return data

    def resolve_deps(datablock: object) -> [object]:
        deps = []

        if self.instance.use_nodes:
            deps.extend(get_node_tree_dependencies(self.instance.node_tree))
        if self.is_library:
            deps.append(self.instance.library)
        return deps
