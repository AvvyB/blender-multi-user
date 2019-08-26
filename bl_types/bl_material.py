import bpy
import mathutils

from .. import utils
from .bl_datablock import BlDatablock

class BlMaterial(BlDatablock):
    def __init__(self, *args, **kwargs):
        self.icon = 'MATERIAL_DATA'

        super().__init__( *args, **kwargs)
        
    def construct(self, data):
        return bpy.data.materials.new(data["name"])

    def load(self, data, target):
        if data['is_grease_pencil']:
            if not target.is_grease_pencil:
                bpy.data.materials.create_gpencil_data(target)

            utils.dump_anything.load(target.grease_pencil, data['grease_pencil'])

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
                        continue

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
            utils.dump_datablock_attibutes(
                pointer.node_tree, ["nodes", "links"], 5, data['node_tree'])
        elif pointer.is_grease_pencil:
            utils.dump_datablock_attibutes(pointer, ["grease_pencil"], 3, data)
        return data
    
    def resolve(self):
        assert(self.buffer)      
        self.pointer = bpy.data.materials.get(self.buffer['name'])

    def diff(self):
        if self.pointer.is_grease_pencil:
            self.dump(pointer=self.pointer) != self.buffer
        else:
            return len(self.pointer.node_tree.links) != len(self.buffer['node_tree']['links'])
bl_id = "materials"
bl_class = bpy.types.Material
bl_rep_class = BlMaterial
bl_delay_refresh = 1
bl_delay_apply = 1
