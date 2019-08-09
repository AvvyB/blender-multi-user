import bpy
import mathutils
import os

from .. import utils, environment
from ..libs.replication.data import ReplicatedDatablock

class BlImage(ReplicatedDatablock):
    def __init__(self, *args, **kwargs):
        self.icon = 'IMAGE_DATA'

        super().__init__( *args, **kwargs)
        
    def load(self, data, target):
        if not target:
            image = bpy.data.images.new(
                name=data['name'],
                width=data['size'][0],
                height=data['size'][1]
            )
        else:
            image = target

        img_name = "{}.png".format(image.name)

        img_path = os.path.join(environment.CACHE_DIR, img_name)

        file = open(img_path, 'wb')
        file.write(data["pixels"])
        file.close()

        image.source = 'FILE'
        image.filepath = img_path


    def dump(self, pointer=None):
        assert(pointer)
        data = {}
        data['pixels'] = utils.dump_image(pointer)
        utils.dump_datablock_attibutes(pointer, [], 2, data)
        data = utils.dump_datablock_attibutes(
            pointer, 
            ["name", 'size', 'height', 'alpha', 'float_buffer', 'filepath', 'source'],
            2,
            data)
        return data

bl_id = "images"
bl_class = bpy.types.Image
bl_rep_class = BlImage

