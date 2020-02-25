import bpy
import mathutils
import os

from .. import utils, environment
from .bl_datablock import BlDatablock

def dump_image(image):
    pixels = None
    if image.source == "GENERATED":
        img_name = "{}.png".format(image.name)

        image.filepath_raw = os.path.join(environment.CACHE_DIR, img_name)
        image.file_format = "PNG"
        image.save()

    if image.source == "FILE":
        image_path = bpy.path.abspath(image.filepath_raw)
        image_directory = os.path.dirname(image_path)
        os.makedirs(image_directory, exist_ok=True)
        image.save()
        file = open(image_path, "rb")
        pixels = file.read()
        file.close()
    else:
        raise ValueError()
    return pixels

class BlImage(BlDatablock):
    bl_id = "images"
    bl_class = bpy.types.Image
    bl_delay_refresh = 0
    bl_delay_apply = 1
    bl_automatic_push = False
    bl_icon = 'IMAGE_DATA'

    def construct(self, data):
        return bpy.data.images.new(
                name=data['name'],
                width=data['size'][0],
                height=data['size'][1]
            )

    def load(self, data, target):
        image = target

        img_name = "{}.png".format(image.name)

        img_path = os.path.join(environment.CACHE_DIR, img_name)

        file = open(img_path, 'wb')
        file.write(data["pixels"])
        file.close()

        image.source = 'FILE'
        image.filepath = img_path


    def dump_implementation(self, data, pointer=None):
        assert(pointer)
        data = {}
        data['pixels'] = dump_image(pointer)
        utils.dump_datablock_attibutes(pointer, [], 2, data)
        data = utils.dump_datablock_attibutes(
            pointer, 
            ["name", 'size', 'height', 'alpha', 'float_buffer', 'filepath', 'source'],
            2,
            data)
        return data

    def diff(self):
        return False
    
    def is_valid(self):
        return bpy.data.images.get(self.data['name'])
