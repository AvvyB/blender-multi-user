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
from .bl_datablock import BlDatablock
from .bl_material import load_links, load_node, dump_node, dump_links


class BlWorld(BlDatablock):
    bl_id = "worlds"
    bl_class = bpy.types.World
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'WORLD_DATA'

    def _construct(self, data):
        return bpy.data.worlds.new(data["name"])

    def _load_implementation(self, data, target):
        if data["use_nodes"]:
            if target.node_tree is None:
                target.use_nodes = True

            target.node_tree.nodes.clear()

            for node in data["node_tree"]["nodes"]:
                load_node(data["node_tree"]["nodes"][node], target.node_tree)

            # Load nodes links
            target.node_tree.links.clear()

            
            load_links(data["node_tree"]["links"], target.node_tree)

    def _dump_implementation(self, data, instance=None):
        assert(instance)

        world_dumper = Dumper()
        world_dumper.depth = 2
        world_dumper.exclude_filter = [
            "preview",
            "original",
            "uuid",
            "color",
            "cycles",
            "light_settings",
            "users",
            "view_center"
        ]
        data = world_dumper.dump(instance)
        if instance.use_nodes:
            nodes = {}

            for node in instance.node_tree.nodes:
                nodes[node.name] = dump_node(node)

            data["node_tree"]['nodes'] = nodes

            data["node_tree"]['links'] = dump_links(instance.node_tree.links)

        return data

    def _resolve_deps_implementation(self):
        deps = []

        if self.instance.use_nodes:
            for node in self.instance.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    deps.append(node.image)
        if self.is_library:
            deps.append(self.instance.library)
        return deps

