import bpy
import mathutils
from jsondiff import diff

from ..libs.overrider import Overrider
from .. import utils
from .. import presence
from .bl_datablock import BlDatablock


class BlArmature(BlDatablock):
    def construct(self, data):
        return bpy.data.armatures.new(data["name"])

    def load(self, data, target):
        # Load parent object
        if data['user'] not in bpy.data.objects:
            parent_object = bpy.data.objects.new(data['user'],self.pointer)
        else:
            parent_object = bpy.data.objects['user']
        
        # Link it to the correct context
        if  data['user_collection'][0] not in bpy.data.collections:
            parent_collection = bpy.data.collections.new(data['user_collection'][0])
        else:
            parent_collection =  bpy.data.collection['user_collection'][0]
        parent_collection.objects.link(parent_object)

        # utils.dump_anything.load(target, data)
        # with Overrider(name="bpy_",parent=bpy.context) as bpy_:
        area, region, rv3d = presence.view3d_find()

        override = bpy.context.copy()
        override['window'] = bpy.data.window_managers[0].windows[0]
        override['area'] = area
        override['region'] = region
        override['screen'] = bpy.data.window_managers[0].windows[0].screen
        override['active_object'] = parent_object
        override['selected_objects'] = [parent_object]
        try:
            bpy.ops.object.mode_set(override,mode='EDIT')
        except Exception as e:
            print(e)
            # bpy_.mode =  'EDIT_ARMATURE'

            # bpy_.active_object = armature
            # bpy_.selected_objects = [armature]

    def dump(self, pointer=None):
        assert(pointer)
        data =  utils.dump_datablock(pointer, 3)

        #get the parent Object
        object_users = utils.get_users(pointer)[0]
        data['user'] = object_users.name

        #get parent collection
        container_users = utils.get_users(object_users)
        data['user_collection'] = [item.name for item in container_users if isinstance(item,bpy.types.Collection)]
        data['user_scene'] = [item.name for item in container_users if isinstance(item,bpy.types.Scene)]
        return data

    def resolve(self):
        assert(self.buffer)
        self.pointer = bpy.data.armatures.get(self.buffer['name'])

    def diff(self):
        False


bl_id = "armatures"
bl_class = bpy.types.Armature
bl_rep_class = BlArmature
bl_delay_refresh = 1
bl_delay_apply = 1
bl_automatic_push = True
bl_icon = 'ARMATURE_DATA'