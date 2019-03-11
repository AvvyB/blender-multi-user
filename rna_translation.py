from . import net_components
import bpy
import mathutils

def set_vector(value):
    return  [value.x, value.y, value.z]

def get_vector(value):
    return mathutils.Vector(
            (value[0], value[1], value[2]))

class RNAFactory(net_components.RCFFactory):
    def load_getter(self, data):
        print("load RNA getter")
        getter = None
        if isinstance(data.body, mathutils.Vector):
            print("Vector")
            getter = get_vector

        return getter
    
    def load_setter(self,data):
        print("load RNA setter")
        setter = None
        if isinstance(data.body, mathutils.Vector):
            print("Vector")     
            setter = set_vector
        
        return setter