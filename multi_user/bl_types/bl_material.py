import bpy
import mathutils
import logging
from jsondiff import diff

from .. import utils
from .bl_datablock import BlDatablock

logger = logging.getLogger(__name__)

def load_node(target_node_tree, source):
    target_node = target_node_tree.nodes.get(source["name"])

    if target_node is None:
        node_type = source["bl_idname"]

        target_node = target_node_tree.nodes.new(type=node_type)

    utils.dump_anything.load(
        target_node, source)

    if source['type'] == 'TEX_IMAGE':
        target_node.image = bpy.data.images[source['image']]

    for input in source["inputs"]:
        if hasattr(target_node.inputs[input], "default_value"):
            try:
                target_node.inputs[input].default_value = source["inputs"][input]["default_value"]
            except:
                logger.error("{} not supported, skipping".format(input))

def load_link(target_node_tree, source):
    input_socket = target_node_tree.nodes[source['to_node']
                                          ['name']].inputs[source['to_socket']['name']]
    output_socket = target_node_tree.nodes[source['from_node']
                                           ['name']].outputs[source['from_socket']['name']]

    target_node_tree.links.new(input_socket, output_socket)


class BlMaterial(BlDatablock):
    def construct(self, data):
        return bpy.data.materials.new(data["name"])

    def load(self, data, target):
        if data['is_grease_pencil']:
            if not target.is_grease_pencil:
                bpy.data.materials.create_gpencil_data(target)

            utils.dump_anything.load(
                target.grease_pencil, data['grease_pencil'])

            utils.load_dict(data['grease_pencil'], target.grease_pencil)

        elif data["use_nodes"]:
            if target.node_tree is None:
                target.use_nodes = True

            target.node_tree.nodes.clear()

            # Load nodes
            for node in data["node_tree"]["nodes"]:
                load_node(target.node_tree, data["node_tree"]["nodes"][node])

            # Load nodes links
            target.node_tree.links.clear()

            for link in data["node_tree"]["links"]:
                load_link(target.node_tree, data["node_tree"]["links"][link])

    def dump(self, pointer=None):
        assert(pointer)
        mat_dumper = utils.dump_anything.Dumper()
        mat_dumper.depth = 2
        mat_dumper.exclude_filter = [
            "preview",
            "original",
            "uuid",
            "users",
            "alpha_threshold",
            "line_color",
            "view_center",
        ]
        node_dumper = utils.dump_anything.Dumper()
        node_dumper.depth = 1
        node_dumper.exclude_filter = [
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
            "width_hidden"
        ]
        input_dumper = utils.dump_anything.Dumper()
        input_dumper.depth = 2
        input_dumper.include_filter = ["default_value"]
        links_dumper = utils.dump_anything.Dumper()
        links_dumper.depth = 3
        links_dumper.exclude_filter = ["dimensions"]
        data = mat_dumper.dump(pointer)

        if pointer.use_nodes:
            nodes = {}

            for node in pointer.node_tree.nodes:
                nodes[node.name] = node_dumper.dump(node)

                if hasattr(node, 'inputs'):
                    nodes[node.name]['inputs'] = {}

                    for i in node.inputs:
                        
                        if hasattr(i, 'default_value'):
                            nodes[node.name]['inputs'][i.name] = input_dumper.dump(
                                i)
            data["node_tree"]['nodes'] = nodes
            data["node_tree"]["links"] = links_dumper.dump(pointer.node_tree.links)
        
        elif pointer.is_grease_pencil:
            utils.dump_datablock_attibutes(pointer, ["grease_pencil"], 3, data)
        return data

    def resolve(self):
        assert(self.buffer)
        self.pointer = bpy.data.materials.get(self.buffer['name'])

    def resolve_dependencies(self):
        # TODO: resolve node group deps
        deps = []

        if self.pointer.use_nodes:
            for node in self.pointer.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    deps.append(node.image)
        if self.is_library:
            deps.append(self.pointer.library)

        return deps

    def is_valid(self):
        return bpy.data.materials.get(self.buffer['name'])


bl_id = "materials"
bl_class = bpy.types.Material
bl_rep_class = BlMaterial
bl_delay_refresh = 10
bl_delay_apply = 10
bl_automatic_push = True
bl_icon = 'MATERIAL_DATA'
