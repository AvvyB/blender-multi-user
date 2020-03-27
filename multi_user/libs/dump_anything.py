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

import logging

import bpy
import bpy.types as T
import mathutils

logger = logging.getLogger(__name__)

def remove_items_from_dict(d, keys, recursive=False):
    copy = dict(d)
    for k in keys:
        copy.pop(k, None)
    if recursive:
        for k in [k for k in copy.keys() if isinstance(copy[k], dict)]:
            copy[k] = remove_items_from_dict(copy[k], keys, recursive)
    return copy


def _is_dictionnary(v):
    return hasattr(v, "items") and callable(v.items)


def _dump_filter_type(t):
    return lambda x: isinstance(x, t)


def _dump_filter_type_by_name(t_name):
    return lambda x: t_name == x.__class__.__name__


def _dump_filter_array(array):
    # only primitive type array
    if not isinstance(array, T.bpy_prop_array):
        return False
    if len(array) > 0 and type(array[0]) not in [bool, float, int]:
        return False
    return True


def _dump_filter_default(default):
    if default is None:
        return False
    if type(default) is list:
        return False
    return True


def _load_filter_type(t, use_bl_rna=True):
    def filter_function(x):
        if use_bl_rna and x.bl_rna_property:
            return isinstance(x.bl_rna_property, t)
        else:
            return isinstance(x.read(), t)
    return filter_function


def _load_filter_array(array):
    # only primitive type array
    if not isinstance(array.read(), T.bpy_prop_array):
        return False
    if len(array.read()) > 0 and type(array.read()[0]) not in [bool, float, int]:
        return False
    return True


def _load_filter_color(color):
    return color.__class__.__name__ == 'Color'


def _load_filter_default(default):
    if default.read() is None:
        return False
    if type(default.read()) is list:
        return False
    return True


class Dumper:
    # TODO: support occlude readonly  
    def __init__(self):
        self.verbose = True
        self.depth = 1
        self.keep_compounds_as_leaves = False
        self.accept_read_only = True
        self._build_inline_dump_functions()
        self._build_match_elements()
        self.type_subset = self.match_subset_all
        self.include_filter = []
        self.exclude_filter = []

    def dump(self, any):
        return self._dump_any(any, 0)

    def _dump_any(self, any, depth):
        for filter_function, dump_function in self.type_subset:
            if filter_function(any):
                return dump_function[not (depth >= self.depth)](any, depth + 1)

    def _build_inline_dump_functions(self):
        self._dump_identity = (lambda x, depth: x, lambda x, depth: x)
        self._dump_ref = (lambda x, depth: x.name, self._dump_object_as_branch)
        self._dump_ID = (lambda x, depth: x.name, self._dump_default_as_branch)
        self._dump_collection = (
            self._dump_default_as_leaf, self._dump_collection_as_branch)
        self._dump_array = (self._dump_default_as_leaf,
                            self._dump_array_as_branch)
        self._dump_matrix = (self._dump_matrix_as_leaf,
                             self._dump_matrix_as_leaf)
        self._dump_vector = (self._dump_vector_as_leaf,
                             self._dump_vector_as_leaf)
        self._dump_quaternion = (
            self._dump_quaternion_as_leaf, self._dump_quaternion_as_leaf)
        self._dump_default = (self._dump_default_as_leaf,
                              self._dump_default_as_branch)
        self._dump_color = (self._dump_color_as_leaf, self._dump_color_as_leaf)

    def _build_match_elements(self):
        self._match_type_bool = (_dump_filter_type(bool), self._dump_identity)
        self._match_type_int = (_dump_filter_type(int), self._dump_identity)
        self._match_type_float = (
            _dump_filter_type(float), self._dump_identity)
        self._match_type_string = (_dump_filter_type(str), self._dump_identity)
        self._match_type_ref = (_dump_filter_type(T.Object), self._dump_ref)
        self._match_type_ID = (_dump_filter_type(T.ID), self._dump_ID)
        self._match_type_bpy_prop_collection = (
            _dump_filter_type(T.bpy_prop_collection), self._dump_collection)
        self._match_type_array = (_dump_filter_array, self._dump_array)
        self._match_type_matrix = (_dump_filter_type(
            mathutils.Matrix), self._dump_matrix)
        self._match_type_vector = (_dump_filter_type(
            mathutils.Vector), self._dump_vector)
        self._match_type_quaternion = (_dump_filter_type(
            mathutils.Quaternion), self._dump_quaternion)
        self._match_type_euler = (_dump_filter_type(
            mathutils.Euler), self._dump_quaternion)
        self._match_type_color = (
            _dump_filter_type_by_name("Color"), self._dump_color)
        self._match_default = (_dump_filter_default, self._dump_default)

    def _dump_collection_as_branch(self, collection, depth):
        dump = {}
        for i in collection.items():
            dv = self._dump_any(i[1], depth)
            if not (dv is None):
                dump[i[0]] = dv
        return dump

    def _dump_default_as_leaf(self, default, depth):
        if self.keep_compounds_as_leaves:
            return str(type(default))
        else:
            return None

    def _dump_array_as_branch(self, array, depth):
        return [i for i in array]

    def _dump_matrix_as_leaf(self, matrix, depth):
        return [list(v) for v in matrix]

    def _dump_vector_as_leaf(self, vector, depth):
        return list(vector)

    def _dump_quaternion_as_leaf(self, quaternion, depth):
        return list(quaternion)

    def _dump_color_as_leaf(self, color, depth):
        return list(color)

    def _dump_object_as_branch(self, default, depth):
        if depth == 1:
            return self._dump_default_as_branch(default, depth)
        else:
            return default.name

    def _dump_default_as_branch(self, default, depth):
        def is_valid_property(p):
            try:
                if (self.include_filter and p not in self.include_filter):
                    return False
                getattr(default, p)
            except AttributeError as err:
                logger.debug(err)
                return False
            if p.startswith("__"):
                return False
            if callable(getattr(default, p)):
                return False
            if p in ["bl_rna", "rna_type"]:
                return False
            return True

        all_property_names = [p for p in dir(default) if is_valid_property(
            p) and p != '' and p not in self.exclude_filter]
        dump = {}
        for p in all_property_names:
            if (self.exclude_filter and p in self.exclude_filter) or\
                    (self.include_filter and p not in self.include_filter):
                return False
            dp = self._dump_any(getattr(default, p), depth)
            if not (dp is None):
                dump[p] = dp
        return dump

    @property
    def match_subset_all(self):
        return [
            self._match_type_bool,
            self._match_type_int,
            self._match_type_float,
            self._match_type_string,
            self._match_type_ref,
            self._match_type_ID,
            self._match_type_bpy_prop_collection,
            self._match_type_array,
            self._match_type_matrix,
            self._match_type_vector,
            self._match_type_quaternion,
            self._match_type_euler,
            self._match_type_color,
            self._match_default
        ]

    @property
    def match_subset_primitives(self):
        return [
            self._match_type_bool,
            self._match_type_int,
            self._match_type_float,
            self._match_type_string,
            self._match_default
        ]


class BlenderAPIElement:
    def __init__(self, api_element, sub_element_name="", occlude_read_only=True):
        self.api_element = api_element
        self.sub_element_name = sub_element_name
        self.occlude_read_only = occlude_read_only

    def read(self):
        return getattr(self.api_element, self.sub_element_name) if self.sub_element_name else self.api_element

    def write(self, value):
        # take precaution if property is read-only
        if self.sub_element_name and \
            not self.api_element.is_property_readonly(self.sub_element_name):
        
            setattr(self.api_element, self.sub_element_name, value)
        else:
            self.api_element = value

    def extend(self, element_name):
        return BlenderAPIElement(self.read(), element_name)

    @property
    def bl_rna_property(self):
        if not hasattr(self.api_element, "bl_rna"):
            return False
        if not self.sub_element_name:
            return False
        return self.api_element.bl_rna.properties[self.sub_element_name]


class Loader:
    def __init__(self):
        self.type_subset = self.match_subset_all
        self.occlude_read_only = False
        self.order = ['*']

    def load(self, dst_data, src_dumped_data):
        self._load_any(
            BlenderAPIElement(
                dst_data, occlude_read_only=self.occlude_read_only),
            src_dumped_data
        )

    def _load_any(self, any, dump):
        for filter_function, load_function in self.type_subset:
            if filter_function(any):
                load_function(any, dump)
                return

    def _load_identity(self, element, dump):
        element.write(dump)

    def _load_array(self, element, dump):
        # supports only primitive types currently
        try:
            for i in range(len(dump)):
                element.read()[i] = dump[i]
        except AttributeError as err:
            logger.debug(err)
            if not self.occlude_read_only:
                raise err

    def _load_collection(self, element, dump):
        if not element.bl_rna_property:
            return
        # local enum
        CONSTRUCTOR_NEW = "new"
        CONSTRUCTOR_ADD = "add"

        DESTRUCTOR_REMOVE = "remove"
        DESTRUCTOR_CLEAR = "clear"
 
        constructors = {
            T.ColorRampElement: (CONSTRUCTOR_NEW, ["position"]),
            T.ParticleSettingsTextureSlot: (CONSTRUCTOR_ADD, []),
            T.Modifier: (CONSTRUCTOR_NEW, ["name", "type"]),
            T.Constraint: (CONSTRUCTOR_NEW, ["type"]),
            # T.VertexGroup: (CONSTRUCTOR_NEW, ["name"], True),
        }

        destructors = {
            T.ColorRampElement:DESTRUCTOR_REMOVE,
            T.Modifier: DESTRUCTOR_CLEAR,
            T.Constraint: CONSTRUCTOR_NEW,
        }
        element_type = element.bl_rna_property.fixed_type
        
        constructor = constructors.get(type(element_type))

        if constructor is None:  # collection type not supported
            return

        destructor  = destructors.get(type(element_type))

        # Try to clear existing 
        if destructor:
            if destructor == DESTRUCTOR_REMOVE:
                collection = element.read()
                for i in range(len(collection)-1):
                    collection.remove(collection[0])
            else:
                getattr(element.read(), DESTRUCTOR_CLEAR)()
        
        for dump_idx, dumped_element in enumerate(dump.values()):
            if dump_idx == 0 and len(element.read())>0:
                new_element = element.read()[0]       
            else:
                try:
                    constructor_parameters = [dumped_element[name]
                                            for name in constructor[1]]
                except KeyError:
                    logger.debug("Collection load error, missing parameters.")
                    continue  # TODO handle error
                
                new_element = getattr(element.read(), constructor[0])(
                    *constructor_parameters)
            self._load_any(
                BlenderAPIElement(
                    new_element, occlude_read_only=self.occlude_read_only),
                dumped_element
            )

    def _load_curve_mapping(self, element, dump):
        mapping = element.read()
        # cleanup existing curve
        for curve in mapping.curves:
            for idx in range(len(curve.points)):
                if idx == 0:
                    break

                curve.points.remove(curve.points[1])
        for curve_index, curve in dump['curves'].items():
            for point_idx, point in curve['points'].items():
                pos = point['location']
                
                if len(mapping.curves[curve_index].points) == 1:
                    mapping.curves[curve_index].points[int(point_idx)].location = pos
                else:
                    mapping.curves[curve_index].points.new(pos[0],pos[1])

    def _load_pointer(self, pointer, dump):
        rna_property_type = pointer.bl_rna_property.fixed_type
        if not rna_property_type:
            return
        if isinstance(rna_property_type, T.Image):
            pointer.write(bpy.data.images.get(dump))
        elif isinstance(rna_property_type, T.Texture):
            pointer.write(bpy.data.textures.get(dump))
        elif isinstance(rna_property_type, T.ColorRamp):
            self._load_default(pointer, dump)
        elif isinstance(rna_property_type, T.Object):
            pointer.write(bpy.data.objects.get(dump))
        elif isinstance(rna_property_type, T.Mesh):
            pointer.write(bpy.data.meshes.get(dump))
        elif isinstance(rna_property_type, T.Material):
            pointer.write(bpy.data.materials.get(dump))
        elif isinstance(rna_property_type, T.Collection):
            pointer.write(bpy.data.collections.get(dump))

    def _load_matrix(self, matrix, dump):
        matrix.write(mathutils.Matrix(dump))

    def _load_vector(self, vector, dump):
        vector.write(mathutils.Vector(dump))

    def _load_quaternion(self, quaternion, dump):
        quaternion.write(mathutils.Quaternion(dump))

    def _load_euler(self, euler, dump):
        euler.write(mathutils.Euler(dump))

    def _ordered_keys(self, keys):
        ordered_keys = []
        for order_element in self.order:
            if order_element == '*':
                ordered_keys += [k for k in keys if not k in self.order]
            else:
                if order_element in keys:
                    ordered_keys.append(order_element)
        return ordered_keys

    def _load_default(self, default, dump):
        if not _is_dictionnary(dump):
            return  # TODO error handling
        for k in self._ordered_keys(dump.keys()):
            v = dump[k]
            if not hasattr(default.read(), k):
                logger.debug(f"Load default, skipping {default} : {k}")
            try:
                self._load_any(default.extend(k), v)
            except Exception as err:
                logger.debug(f"Cannot load {k}: {err}")

    @property
    def match_subset_all(self):
        return [
            (_load_filter_type(T.BoolProperty), self._load_identity),
            (_load_filter_type(T.IntProperty), self._load_identity),
            # before float because bl_rna type of matrix if FloatProperty
            (_load_filter_type(mathutils.Matrix, use_bl_rna=False), self._load_matrix),
            # before float because bl_rna type of vector if FloatProperty
            (_load_filter_type(mathutils.Vector, use_bl_rna=False), self._load_vector),
            (_load_filter_type(mathutils.Quaternion, use_bl_rna=False), self._load_quaternion),
            (_load_filter_type(mathutils.Euler, use_bl_rna=False), self._load_euler),
            (_load_filter_type(T.CurveMapping,  use_bl_rna=False), self._load_curve_mapping),
            (_load_filter_type(T.FloatProperty), self._load_identity),
            (_load_filter_type(T.StringProperty), self._load_identity),
            (_load_filter_type(T.EnumProperty), self._load_identity),
            (_load_filter_type(T.PointerProperty), self._load_pointer),
            (_load_filter_array, self._load_array),
            (_load_filter_type(T.CollectionProperty), self._load_collection),
            (_load_filter_default, self._load_default),
            (_load_filter_color, self._load_identity),
        ]


# Utility functions
def dump(any, depth=1):
    dumper = Dumper()
    dumper.depth = depth
    return dumper.dump(any)


def load(dst, src):
    loader = Loader()
    loader.load(dst, src)
