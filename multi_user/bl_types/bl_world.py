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
from .bl_datablock import BlDatablock
from .bl_material import load_links, load_node, dump_links


class BlWorld(BlDatablock):
    bl_id = "worlds"
    bl_class = bpy.types.World
    bl_delay_refresh = 4
    bl_delay_apply = 4
    bl_automatic_push = True
    bl_icon = 'WORLD_DATA'

    def _construct(self, data):
        return bpy.data.worlds.new(data["name"])

    def load_implementation(self, data, target):
        if data["use_nodes"]:
            if target.node_tree is None:
                target.use_nodes = True

            target.node_tree.nodes.clear()

            for node in data["node_tree"]["nodes"]:
                load_node(data["node_tree"]["nodes"][node], target.node_tree)

            # Load nodes links
            target.node_tree.links.clear()

            
            load_links(data["node_tree"]["links"], target.node_tree)

    def dump_implementation(self, data, pointer=None):
        assert(pointer)

        world_dumper = utils.dump_anything.Dumper()
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
        data = world_dumper.dump(pointer)
        if pointer.use_nodes:
            nodes = {}
            dumper = utils.dump_anything.Dumper()
            dumper.depth = 2
            dumper.exclude_filter = [
                "dimensions",
                "select",
                "bl_height_min",
                "bl_height_max",
                "bl_width_min",
                "bl_width_max",
                "bl_width_default",
                "hide",
                "show_options",
                "show_tetxures",
                "show_preview",
                "outputs",
                "preview",
                "original",
                "width_hidden",
                
            ]

            for node in pointer.node_tree.nodes:
                nodes[node.name] = dumper.dump(node)

                if hasattr(node, 'inputs'):
                    nodes[node.name]['inputs'] = {}

                    for i in node.inputs:
                        input_dumper = utils.dump_anything.Dumper()
                        input_dumper.depth = 2
                        input_dumper.include_filter = ["default_value"]
                        if hasattr(i, 'default_value'):
                            nodes[node.name]['inputs'][i.name] = input_dumper.dump(
                                i)
            data["node_tree"]['nodes'] = nodes

            data["node_tree"]['links'] = dump_links(pointer.node_tree.links)

        return data

    def resolve_deps_implementation(self):
        deps = []

        if self.pointer.use_nodes:
            for node in self.pointer.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    deps.append(node.image)
        if self.is_library:
            deps.append(self.pointer.library)
        return deps

