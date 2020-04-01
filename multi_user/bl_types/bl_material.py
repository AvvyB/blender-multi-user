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
import logging

from .. import utils
from .dump_anything import Loader, Dumper
from .bl_datablock import BlDatablock

logger = logging.getLogger(__name__)

def load_node(node_data, node_tree):
    """ Load a node into a node_tree from a dict

        :arg node_data: dumped node data
        :type node_data: dict
        :arg node_tree: target node_tree
        :type node_tree: bpy.types.NodeTree
    """
    loader = Loader()
    target_node = node_tree.nodes.new(type=node_data["bl_idname"])

    loader.load(target_node, node_data)    

    

    for input in node_data["inputs"]:
        if hasattr(target_node.inputs[input], "default_value"):
            try:
                target_node.inputs[input].default_value = node_data["inputs"][input]["default_value"]
            except:
                logger.error("{} not supported, skipping".format(input))


def load_links(links_data, node_tree):
    """ Load node_tree links from a list
        
        :arg links_data: dumped node links
        :type links_data: list
        :arg node_tree: node links collection
        :type node_tree: bpy.types.NodeTree
    """

    for link in links_data:
        input_socket = node_tree.nodes[link['to_node']].inputs[int(link['to_socket'])]
        output_socket = node_tree.nodes[link['from_node']].outputs[int(link['from_socket'])]

        node_tree.links.new(input_socket, output_socket)


def dump_links(links):
    """ Dump node_tree links collection to a list

        :arg links: node links collection
        :type links: bpy.types.NodeLinks
        :retrun: list
    """

    links_data = []

    for link in links:
        links_data.append({
            'to_node':link.to_node.name,
            'to_socket':link.to_socket.path_from_id()[-2:-1],
            'from_node':link.from_node.name,
            'from_socket':link.from_socket.path_from_id()[-2:-1],
        })

    return links_data


def dump_node(node):
    """ Dump a single node to a dict

        :arg node: target node
        :type node: bpy.types.Node
        :retrun: dict
    """

    node_dumper = Dumper()
    node_dumper.depth = 1
    node_dumper.exclude_filter = [
        "dimensions",
        "show_expanded",
        "name_full",
        "select",
        "bl_height_min",
        "bl_height_max",
        "bl_height_default",
        "bl_width_min",
        "bl_width_max",
        "type",
        "bl_icon",
        "bl_width_default",
        "bl_static_type",
        "show_tetxure",
        "is_active_output",
        "hide",
        "show_options",
        "show_preview",
        "show_texture",
        "outputs",
        "width_hidden"
    ]
    
    dumped_node = node_dumper.dump(node)

    if hasattr(node, 'inputs'):
        dumped_node['inputs'] = {}

        for i in node.inputs:
            input_dumper = Dumper()
            input_dumper.depth = 2
            input_dumper.include_filter = ["default_value"]

            if hasattr(i, 'default_value'):
                dumped_node['inputs'][i.name] = input_dumper.dump(
                    i)
    if hasattr(node, 'color_ramp'):
        ramp_dumper = Dumper()
        ramp_dumper.depth = 4
        ramp_dumper.include_filter = [
            'elements',
            'alpha',
            'color',
            'position'
        ]
        dumped_node['color_ramp'] = ramp_dumper.dump(node.color_ramp)
    if hasattr(node, 'mapping'):
        curve_dumper = Dumper()
        curve_dumper.depth = 5
        curve_dumper.include_filter = [
            'curves',
            'points',
            'location'
        ]
        dumped_node['mapping'] = curve_dumper.dump(node.mapping)
    
    return dumped_node


class BlMaterial(BlDatablock):
    bl_id = "materials"
    bl_class = bpy.types.Material
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_icon = 'MATERIAL_DATA'

    def _construct(self, data):
        return bpy.data.materials.new(data["name"])

    def _load_implementation(self, data, target):
        loader = Loader()
        target.name = data['name']
        if data['is_grease_pencil']:
            if not target.is_grease_pencil:
                bpy.data.materials.create_gpencil_data(target)

            loader.load(
                target.grease_pencil, data['grease_pencil'])


        elif data["use_nodes"]:
            if target.node_tree is None:
                target.use_nodes = True

            target.node_tree.nodes.clear()

            loader.load(target,data)
            
            # Load nodes
            for node in data["node_tree"]["nodes"]:
                load_node(data["node_tree"]["nodes"][node], target.node_tree)

            # Load nodes links
            target.node_tree.links.clear()

            load_links(data["node_tree"]["links"], target.node_tree)

    def _dump_implementation(self, data, pointer=None):
        assert(pointer)
        mat_dumper = Dumper()
        mat_dumper.depth = 2
        mat_dumper.exclude_filter = [
            "is_embed_data",
            "is_evaluated",
            "name_full",
            "bl_description",
            "bl_icon",
            "bl_idname",
            "bl_label",
            "preview",
            "original",
            "uuid",
            "users",
            "alpha_threshold",
            "line_color",
            "view_center",
        ]
        data = mat_dumper.dump(pointer)

        if pointer.use_nodes:
            nodes = {}
            for node in pointer.node_tree.nodes:
                nodes[node.name] = dump_node(node)
            data["node_tree"]['nodes'] = nodes
            
            data["node_tree"]["links"] = dump_links(pointer.node_tree.links)
        elif pointer.is_grease_pencil:
            gp_mat_dumper = Dumper()
            gp_mat_dumper.depth = 3

            gp_mat_dumper.include_filter = [
                'show_stroke',
                'mode',
                'stroke_style',
                'color',
                'use_overlap_strokes',
                'show_fill',
                'fill_style',
                'fill_color',
                'pass_index',
                'alignment_mode',
                # 'fill_image',
                'texture_opacity',
                'mix_factor',
                'texture_offset',
                'texture_angle',
                'texture_scale',
                'texture_clamp',
                'gradient_type',
                'mix_color',
                'flip'                
            ]
            data['grease_pencil'] = gp_mat_dumper.dump(pointer.grease_pencil)
        return data

    def _resolve_deps_implementation(self):
        # TODO: resolve node group deps
        deps = []

        if self.pointer.use_nodes:
            for node in self.pointer.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    deps.append(node.image)
        if self.is_library:
            deps.append(self.pointer.library)

        return deps

