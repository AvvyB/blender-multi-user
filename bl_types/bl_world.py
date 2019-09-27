import bpy
import mathutils
from jsondiff import diff

from .. import utils
from .bl_datablock import BlDatablock
from .bl_material import load_link, load_node


class BlWorld(BlDatablock):
    def construct(self, data):
        return bpy.data.worlds.new(data["name"])

    def load(self, data, target):
        if data["use_nodes"]:
            if target.node_tree is None:
                target.use_nodes = True

            target.node_tree.nodes.clear()

            for node in data["node_tree"]["nodes"]:
                load_node(target.node_tree, data["node_tree"]["nodes"][node])

            # Load nodes links
            target.node_tree.links.clear()

            for link in data["node_tree"]["links"]:
                load_link(target.node_tree, data["node_tree"]["links"][link])

    def dump(self, pointer=None):
        assert(pointer)

        world_dumper = utils.dump_anything.Dumper()
        world_dumper.depth = 2
        world_dumper.exclude_filter = [
            "preview",
            "original",
            "uuid",
            "color"
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
                "width_hidden"
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
            utils.dump_datablock_attibutes(
                pointer.node_tree, ["links"], 3, data['node_tree'])
        return data

    def resolve(self):
        assert(self.buffer)
        self.pointer = bpy.data.worlds.get(self.buffer['name'])

    def diff(self):
        diff_rev = diff(self.dump(pointer=self.pointer), self.buffer)
        print(diff_rev)
        return (self.bl_diff() or
                len(diff_rev.keys()) > 0)

    def resolve_dependencies(self):
        deps = []

        if self.pointer.use_nodes:
            for node in self.pointer.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    deps.append(node.image)
        if self.is_library:
            deps.append(self.pointer.library)

        return deps

    def is_valid(self):
        return bpy.data.worlds.get(self.buffer['name'])


bl_id = "worlds"
bl_class = bpy.types.World
bl_rep_class = BlWorld
bl_delay_refresh = 4
bl_delay_apply = 4
bl_automatic_push = True
bl_icon = 'WORLD_DATA'
