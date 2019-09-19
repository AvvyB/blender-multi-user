import bpy
import mathutils
from jsondiff import diff

from .. import utils
from .bl_datablock import BlDatablock


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

            for node in data["node_tree"]["nodes"]:
                # fix None node tree error

                index = target.node_tree.nodes.find(node)

                if index is -1:
                    node_type = data["node_tree"]["nodes"][node]["bl_idname"]

                    target.node_tree.nodes.new(type=node_type)

                utils.dump_anything.load(
                    target.node_tree.nodes[index], data["node_tree"]["nodes"][node])

                if data["node_tree"]["nodes"][node]['type'] == 'TEX_IMAGE':
                    target.node_tree.nodes[index].image = bpy.data.images[data["node_tree"]
                                                                          ["nodes"][node]['image']['name']]

                for input in data["node_tree"]["nodes"][node]["inputs"]:
                    try:
                        if hasattr(target.node_tree.nodes[index].inputs[input], "default_value"):
                            target.node_tree.nodes[index].inputs[input].default_value = data[
                                "node_tree"]["nodes"][node]["inputs"][input]["default_value"]
                    except Exception as e:
                        print("loading error {}".format(e))
                        continue
                # utils.dump_anything.load(
                #     target.node_tree.nodes[index],data["node_tree"]["nodes"][node])

            # Load nodes links
            target.node_tree.links.clear()

            for link in data["node_tree"]["links"]:
                current_link = data["node_tree"]["links"][link]
                input_socket = target.node_tree.nodes[current_link['to_node']
                                                      ['name']].inputs[current_link['to_socket']['name']]
                output_socket = target.node_tree.nodes[current_link['from_node']
                                                       ['name']].outputs[current_link['from_socket']['name']]

                target.node_tree.links.new(input_socket, output_socket)

    def dump(self, pointer=None):
        assert(pointer)
        data = utils.dump_datablock(pointer, 2)
        if pointer.use_nodes:
            # nodes inputs 
            nodes = {}
            for node in pointer.node_tree.nodes:
                dumper = utils.dump_anything.Dumper()
                if node.type == 'TEX_IMAGE':
                    dumper.depth = 2
                else:
                    dumper.depth = 4

                nodes[node.name] = dumper.dump(node) 
            data["node_tree"]['nodes']= nodes
            utils.dump_datablock_attibutes(
                pointer.node_tree, ["links"], 3, data['node_tree'])
        elif pointer.is_grease_pencil:
            utils.dump_datablock_attibutes(pointer, ["grease_pencil"], 3, data)
        return data

    def resolve(self):
        assert(self.buffer)
        self.pointer = bpy.data.materials.get(self.buffer['name'])

    def diff(self):
        diff_rev = diff(self.dump(pointer=self.pointer), self.buffer)
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
        return bpy.data.materials.get(self.buffer['name'])

bl_id = "materials"
bl_class = bpy.types.Material
bl_rep_class = BlMaterial
bl_delay_refresh = 5
bl_delay_apply = 5
bl_automatic_push = True
bl_icon = 'MATERIAL_DATA'