import bpy
import mathutils
import logging

from .. import utils
from ..libs import dump_anything
from .bl_datablock import BlDatablock

logger = logging.getLogger(__name__)
def clean_color_ramp(target_ramp):
    # clear existing
    try:
        for key in target_ramp.elements:
            target_ramp.elements.remove(key)
    except:
        pass
    
def load_mapping(target_apping, source_mapping):
     # clear existing curves
    for curve in target_apping.curves:
        for point in curve.points:
            try:
                curve.remove(point)
            except:
                continue
    
    # Load curves
    for curve in source_mapping['curves']:
        for point in source_mapping['curves'][curve]['points']:
            pos = source_mapping['curves'][curve]['points'][point]['location']
            target_apping.curves[curve].points.new(pos[0],pos[1])


def load_node(target_node_tree, source):
    target_node = target_node_tree.nodes.get(source["name"])

    if target_node is None:
        node_type = source["bl_idname"]

        target_node = target_node_tree.nodes.new(type=node_type)

    # Clean color ramp before loading it
    if source['type'] == 'VALTORGB':
        clean_color_ramp(target_node.color_ramp)
    if source['type'] == 'CURVE_RGB':
        load_mapping(target_node.mapping, source['mapping'])
    dump_anything.load(
        target_node,
        source)

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
    bl_id = "materials"
    bl_class = bpy.types.Material
    bl_delay_refresh = 10
    bl_delay_apply = 10
    bl_automatic_push = True
    bl_icon = 'MATERIAL_DATA'

    def construct(self, data):
        return bpy.data.materials.new(data["name"])

    def load_implementation(self, data, target):
        target.name = data['name']
        if data['is_grease_pencil']:
            if not target.is_grease_pencil:
                bpy.data.materials.create_gpencil_data(target)

            dump_anything.load(
                target.grease_pencil, data['grease_pencil'])

            utils.load_dict(data['grease_pencil'], target.grease_pencil)

        elif data["use_nodes"]:
            if target.node_tree is None:
                target.use_nodes = True

            target.node_tree.nodes.clear()

            dump_anything.load(target,data)
            
            # Load nodes
            for node in data["node_tree"]["nodes"]:
                load_node(target.node_tree, data["node_tree"]["nodes"][node])

            # Load nodes links
            target.node_tree.links.clear()

            for link in data["node_tree"]["links"]:
                load_link(target.node_tree, data["node_tree"]["links"][link])

    def dump_implementation(self, data, pointer=None):
        assert(pointer)
        mat_dumper = dump_anything.Dumper()
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
        node_dumper = dump_anything.Dumper()
        node_dumper.depth = 1
        node_dumper.exclude_filter = [
            "dimensions",
            "show_expanded"
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
        input_dumper = dump_anything.Dumper()
        input_dumper.depth = 2
        input_dumper.include_filter = ["default_value"]
        links_dumper = dump_anything.Dumper()
        links_dumper.depth = 3
        links_dumper.include_filter = [
            "name",
            "to_node",
            "from_node",
            "from_socket",
            "to_socket"]
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
                if hasattr(node, 'color_ramp'):
                    ramp_dumper = dump_anything.Dumper()
                    ramp_dumper.depth = 4
                    ramp_dumper.include_filter = [
                        'elements',
                        'alpha',
                        'color',
                        'position'
                    ]
                    nodes[node.name]['color_ramp'] = ramp_dumper.dump(node.color_ramp)
                if hasattr(node, 'mapping'):
                    curve_dumper = dump_anything.Dumper()
                    curve_dumper.depth = 5
                    curve_dumper.include_filter = [
                        'curves',
                        'points',
                        'location'
                    ]
                    nodes[node.name]['mapping'] = curve_dumper.dump(node.mapping)
            data["node_tree"]['nodes'] = nodes
            data["node_tree"]["links"] = links_dumper.dump(pointer.node_tree.links)
        
        elif pointer.is_grease_pencil:
            data['grease_pencil'] = dump_anything.dump(pointer.grease_pencil, 3)
        return data

    def resolve_deps_implementation(self):
        # TODO: resolve node group deps
        deps = []

        if self.pointer.use_nodes:
            for node in self.pointer.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    deps.append(node.image)
        if self.is_library:
            deps.append(self.pointer.library)

        return deps

