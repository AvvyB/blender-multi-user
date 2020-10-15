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
import re

from .dump_anything import Loader, Dumper
from .bl_datablock import BlDatablock, get_datablock_from_uuid

NODE_SOCKET_INDEX = re.compile('\[(\d*)\]')


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
    image_uuid = node_data.get('image_uuid', None)

    if image_uuid and not target_node.image:
        target_node.image = get_datablock_from_uuid(image_uuid, None)

    for input in node_data["inputs"]:
        if hasattr(target_node.inputs[input], "default_value"):
            try:
                target_node.inputs[input].default_value = node_data["inputs"][input]["default_value"]
            except:
                logging.error(
                    f"Material {input} parameter not supported, skipping")

    for output in node_data["outputs"]:
        if hasattr(target_node.outputs[output], "default_value"):
            try:
                target_node.outputs[output].default_value = node_data["outputs"][output]["default_value"]
            except:
                logging.error(
                    f"Material {output} parameter not supported, skipping")


def load_links(links_data, node_tree):
    """ Load node_tree links from a list

        :arg links_data: dumped node links
        :type links_data: list
        :arg node_tree: node links collection
        :type node_tree: bpy.types.NodeTree
    """

    for link in links_data:
        input_socket = node_tree.nodes[link['to_node']
                                       ].inputs[int(link['to_socket'])]
        output_socket = node_tree.nodes[link['from_node']].outputs[int(
            link['from_socket'])]
        node_tree.links.new(input_socket, output_socket)


def dump_links(links):
    """ Dump node_tree links collection to a list

        :arg links: node links collection
        :type links: bpy.types.NodeLinks
        :retrun: list
    """

    links_data = []

    for link in links:
        to_socket = NODE_SOCKET_INDEX.search(
            link.to_socket.path_from_id()).group(1)
        from_socket = NODE_SOCKET_INDEX.search(
            link.from_socket.path_from_id()).group(1)
        links_data.append({
            'to_node': link.to_node.name,
            'to_socket': to_socket,
            'from_node': link.from_node.name,
            'from_socket': from_socket,
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
        "bl_label",
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
        "width_hidden",
        "image"
    ]

    dumped_node = node_dumper.dump(node)

    if hasattr(node, 'inputs'):
        dumped_node['inputs'] = {}

        for i in node.inputs:
            input_dumper = Dumper()
            input_dumper.depth = 2
            input_dumper.include_filter = ["default_value"]

            if hasattr(i, 'default_value'):
                dumped_node['inputs'][i.name] = input_dumper.dump(i)

        dumped_node['outputs'] = {}
        for i in node.outputs:
            output_dumper = Dumper()
            output_dumper.depth = 2
            output_dumper.include_filter = ["default_value"]

            if hasattr(i, 'default_value'):
                dumped_node['outputs'][i.name] = output_dumper.dump(i)

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
    if hasattr(node, 'image') and getattr(node, 'image'):
        dumped_node['image_uuid'] = node.image.uuid
    return dumped_node


def get_node_tree_dependencies(node_tree: bpy.types.NodeTree) -> list:
    has_image = lambda node : (node.type in ['TEX_IMAGE', 'TEX_ENVIRONMENT'] and node.image)

    return [node.image for node in node_tree.nodes if has_image(node)]


class BlMaterial(BlDatablock):
    bl_id = "materials"
    bl_class = bpy.types.Material
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = False
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

        if data["use_nodes"]:
            if target.node_tree is None:
                target.use_nodes = True

            target.node_tree.nodes.clear()

            loader.load(target, data)

            # Load nodes
            for node in data["node_tree"]["nodes"]:
                load_node(data["node_tree"]["nodes"][node], target.node_tree)

            # Load nodes links
            target.node_tree.links.clear()

            load_links(data["node_tree"]["links"], target.node_tree)

    def _dump_implementation(self, data, instance=None):
        assert(instance)
        mat_dumper = Dumper()
        mat_dumper.depth = 2
        mat_dumper.include_filter = [
            'name',
            'blend_method',
            'shadow_method',
            'alpha_threshold',
            'show_transparent_back',
            'use_backface_culling',
            'use_screen_refraction',
            'use_sss_translucency',
            'refraction_depth',
            'preview_render_type',
            'use_preview_world',
            'pass_index',
            'use_nodes',
            'diffuse_color',
            'specular_color',
            'roughness',
            'specular_intensity',
            'metallic',
            'line_color',
            'line_priority',
            'is_grease_pencil'
        ]
        data = mat_dumper.dump(instance)

        if instance.use_nodes:
            nodes = {}
            data["node_tree"] = {}
            for node in instance.node_tree.nodes:
                nodes[node.name] = dump_node(node)
            data["node_tree"]['nodes'] = nodes

            data["node_tree"]["links"] = dump_links(instance.node_tree.links)
        elif instance.is_grease_pencil:
            gp_mat_dumper = Dumper()
            gp_mat_dumper.depth = 3

            gp_mat_dumper.include_filter = [
                'color',
                'fill_color',
                'mix_color',
                'mix_factor',
                'mix_stroke_factor',
                # 'texture_angle',
                # 'texture_scale',
                # 'texture_offset',
                'pixel_size',
                'hide',
                'lock',
                'ghost',
                # 'texture_clamp',
                'flip',
                'use_overlap_strokes',
                'show_stroke',
                'show_fill',
                'alignment_mode',
                'pass_index',
                'mode',
                'stroke_style',
                # 'stroke_image',
                'fill_style',
                'gradient_type',
                # 'fill_image',
            ]
            data['grease_pencil'] = gp_mat_dumper.dump(instance.grease_pencil)
        return data

    def _resolve_deps_implementation(self):
        # TODO: resolve node group deps
        deps = []

        if self.instance.use_nodes:
            deps.extend(get_node_tree_dependencies(self.instance.node_tree))
        if self.is_library:
            deps.append(self.instance.library)

        return deps
