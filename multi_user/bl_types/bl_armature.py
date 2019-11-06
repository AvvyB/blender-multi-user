import bpy
import mathutils

from ..libs.overrider import Overrider
from .. import utils
from .. import presence, operators
from .bl_datablock import BlDatablock

# WIP
class BlArmature(BlDatablock):
    def construct(self, data):
        return bpy.data.armatures.new(data["name"])

    def load(self, data, target):
        # Load parent object
        if data['user'] not in bpy.data.objects.keys():
            parent_object = bpy.data.objects.new(data['user'], self.pointer)
        else:
            parent_object = bpy.data.objects[data['user']]
        
        is_object_in_master = (data['user_collection'][0] == "Master Collection")
        #TODO: recursive parent collection loading
        # Link parent object to the collection
        if is_object_in_master:
            parent_collection = bpy.data.scenes[data['user_scene'][0]].collection
        elif  data['user_collection'][0] not in bpy.data.collections.keys():
            parent_collection = bpy.data.collections.new(data['user_collection'][0])
        else:
            parent_collection =  bpy.data.collections[data['user_collection'][0]]
        
        if parent_object.name not in parent_collection.objects:
            parent_collection.objects.link(parent_object)
        
        # Link parent collection to the scene master collection
        if not is_object_in_master and parent_collection.name not in bpy.data.scenes[data['user_scene'][0]].collection.children:
            bpy.data.scenes[data['user_scene'][0]].collection.  children.link(parent_collection)

        area, region, rv3d = presence.view3d_find()
        
        override = bpy.context.copy()
       
        if override['area'] is not None:
            current_mode = bpy.context.mode
            current_active_object = bpy.context.view_layer.objects.active

            # LOAD ARMATURE BONES
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.view_layer.objects.active = parent_object 
            
            bpy.ops.object.mode_set(mode='EDIT')
            print(bpy.context.mode)
        
            for bone in data['bones']:
                if bone not in self.pointer.edit_bones:
                    new_bone = self.pointer.edit_bones.new(bone)
                else:
                    new_bone = self.pointer.edit_bones[bone]
                
                new_bone.tail = data['bones'][bone]['tail_local']
                new_bone.head = data['bones'][bone]['head_local'] 
                new_bone.tail_radius = data['bones'][bone]['tail_radius']
                new_bone.head_radius = data['bones'][bone]['head_radius']

                if 'parent' in data['bones'][bone]:
                    new_bone.parent = self.pointer.edit_bones[data['bones'][bone]['use_connect']['name']]
                    new_bone.use_connect = data['bones'][bone]['use_connect']
            bpy.data.objects['Armature'].update_from_editmode()
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.view_layer.objects.active = current_active_object
            
            # TODO: clean way to restore previous context 
            if 'EDIT' in current_mode :
                bpy.ops.object.mode_set(mode='EDIT')
        else:
            raise Exception("Wrong context")

    def dump_implementation(self, data, pointer=None):
        assert(pointer)

        dumper = utils.dump_anything.Dumper()
        dumper.depth = 3
        dumper.include_filter  = [
            'bones',
            'tail_local',
            'head_local',
            'tail_radius',
            'head_radius',
            'use_connect',
            'name',
            'parent',

        ]
        data = dumper.dump(pointer)
        #get the parent Object
        object_users = utils.get_datablock_users(pointer)[0]
        data['user'] = object_users.name

        #get parent collection
        container_users = utils.get_datablock_users(object_users)
        data['user_collection'] = [item.name for item in container_users if isinstance(item,bpy.types.Collection)]
        data['user_scene'] = [item.name for item in container_users if isinstance(item,bpy.types.Scene)]
        return data

    def resolve(self):
        assert(self.data)
        self.pointer = bpy.data.armatures.get(self.data['name'])

    def is_valid(self):
        return bpy.data.armatures.get(self.data['name'])

bl_id = "armatures"
bl_class = bpy.types.Armature
bl_rep_class = BlArmature
bl_delay_refresh = 1
bl_delay_apply = 0
bl_automatic_push = True
bl_icon = 'ARMATURE_DATA'