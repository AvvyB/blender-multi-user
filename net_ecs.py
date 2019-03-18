import bpy
from .libs.esper import esper

class Object:
    def __init__(self, name=None):
        self.name = name

class Vector:
    def __init__(self, x=0.0 ,y=0.0,z=0.0):
        self.x = x
        self.y = y
        self.z = z

class Pointer:
    def __init__(self, path=None):
        self.path = path

class ObjectProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
            for ent  in self.world.get_component(Object):
                print('asdasd')



class ecs_launch(bpy.types.Operator):
    bl_idname = "ecs.launch"
    bl_label = "ecs_launch"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        
        if event.type == "LEFTMOUSE":
            return {"FINISHED"}
        
        if event.type in {"RIGHTMOUSE", "ESC"}:
            return {"CANCELLED"}
        
        return {"RUNNING_MODAL"}

class ecs_init(bpy.types.Operator):
    bl_idname = "ecs.init"
    bl_label = "ecs_init"
    bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        return {"FINISHED"}


classes = (
    ecs_init,
    ecs_launch,
)


register, unregister = bpy.utils.register_classes_factory(classes)
