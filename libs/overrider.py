"""
Context Manager allowing temporary override of attributes

````python
import bpy
from overrider import Overrider

with Overrider(name='bpy_', parent=bpy) as bpy_:
    # set preview render settings
    bpy_.context.scene.render.use_file_extension = False
    bpy_.context.scene.render.resolution_x = 512
    bpy_.context.scene.render.resolution_y = 512
    bpy_.context.scene.render.use_file_extension = False
    bpy_.context.scene.render.image_settings.file_format = "JPEG"
    bpy_.context.scene.layers[10] = False

    frame_start = action.frame_range[0]
    frame_end = action.frame_range[1]
    if begin_frame is not None:
        frame_start = begin_frame
    if end_frame is not None:
        frame_end = end_frame

    # render
    window = bpy_.data.window_managers[0].windows[0]
    screen = bpy_.data.window_managers[0].windows[0].screen
    area = next(area for area in screen.areas if area.type == 'VIEW_3D')
    space = next(space for space in area.spaces if space.type == 'VIEW_3D')

    space.viewport_shade = 'MATERIAL'
    space.region_3d.view_perspective = 'CAMERA'

    override_context = {
        "window": window._real_value_(),
        "screen": screen._real_value_()
    }

    if frame_start == frame_end:
        bpy.context.scene.frame_set(int(frame_start))
        bpy_.context.scene.render.filepath = os.path.join(directory, "icon.jpg")
        bpy.ops.render.opengl(override_context, write_still=True)

    else:
        for icon_index, frame_number in enumerate(range(int(frame_start), int(frame_end) + 1)):
            bpy.context.scene.frame_set(frame_number)
            bpy.context.scene.render.filepath = os.path.join(directory, "icon", "{:04d}.jpg".format(icon_index))
            bpy.ops.render.opengl(override_context, write_still=True)
````
"""
from collections import OrderedDict


class OverrideIter:

    def __init__(self, parent):
        self.parent = parent
        self.index = -1

    def __next__(self):
        self.index += 1
        try:
            return self.parent[self.index]
        except IndexError as e:
            raise StopIteration


class OverrideBase:

    def __init__(self, context_manager, name=None, parent=None):
        self._name__ = name
        self._context_manager_ = context_manager
        self._parent_ = parent
        self._changed_attributes_ = OrderedDict()
        self._changed_items_ = OrderedDict()
        self._children_ = list()
        self._original_value_ = self._real_value_()

    def __repr__(self):
        return "<{}({})>".format(self.__class__.__name__, self._path_)

    @property
    def _name_(self):
        raise NotImplementedError()

    @property
    def _path_(self):
        if isinstance(self._parent_, OverrideBase):
            return self._parent_._path_ + self._name_

        return self._name_

    def _real_value_(self):
        raise NotImplementedError()

    def _restore_(self):
        for attribute, original_value in reversed(self._changed_attributes_.items()):
            setattr(self._real_value_(), attribute, original_value)

        for item, original_value in reversed(self._changed_items_.items()):
            self._real_value_()[item] = original_value

    def __getattr__(self, attr):
        new_attribute = OverrideAttribute(self._context_manager_, name=attr, parent=self)
        self._children_.append(new_attribute)
        return new_attribute

    def __getitem__(self, item):
        new_item = OverrideItem(self._context_manager_, name=item, parent=self)
        self._children_.append(new_item)
        return new_item

    def __iter__(self):
        return OverrideIter(self)

    def __setattr__(self, attr, value):
        if attr in (
            '_name__',
            '_context_manager_',
            '_parent_',
            '_children_',
            '_original_value_',
            '_changed_attributes_',
            '_changed_items_'
        ):
            self.__dict__[attr] = value
            return

        if attr not in self._changed_attributes_.keys():
            self._changed_attributes_[attr] = getattr(self._real_value_(), attr)
            self._context_manager_.register_as_changed(self)

        setattr(self._real_value_(), attr, value)

    def __setitem__(self, item, value):
        if item not in self._changed_items_.keys():
            self._changed_items_[item] = self._real_value_()[item]
            self._context_manager_.register_as_changed(self)

        self._real_value_()[item] = value

    def __eq__(self, other):
        return self._real_value_() == other

    def __gt__(self, other):
        return self._real_value_() > other

    def __lt__(self, other):
        return self._real_value_() < other

    def __ge__(self, other):
        return self._real_value_() >= other

    def __le__(self, other):
        return self._real_value_() <= other

    def __call__(self, *args, **kwargs):
        # TODO : surround str value with quotes
        arguments = list([str(arg) for arg in args]) + ['{}={}'.format(key, value) for key, value in kwargs.items()]
        arguments = ', '.join(arguments)
        raise RuntimeError('Overrider does not allow call to {}({})'.format(self._path_, arguments))


class OverrideRoot(OverrideBase):

    @property
    def _name_(self):
        return self._name__

    def _real_value_(self):
        return self._parent_


class OverrideAttribute(OverrideBase):

    @property
    def _name_(self):
        return '.{}'.format(self._name__)

    def _real_value_(self):
        return getattr(self._parent_._real_value_(), self._name__)


class OverrideItem(OverrideBase):

    @property
    def _name_(self):
        if isinstance(self._name__, str):
            return '["{}"]'.format(self._name__)

        return '[{}]'.format(self._name__)

    def _real_value_(self):
        return self._parent_._real_value_()[self._name__]


class Overrider:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.override = None
        self.registered_overrides = list()

    def __enter__(self):
        self.override = OverrideRoot(
            context_manager=self,
            parent=self.parent,
            name=self.name
        )
        return self.override

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()

    def register_as_changed(self, override):
        self.registered_overrides.append(override)

    def restore(self):
        for override in reversed(self.registered_overrides):
            override._restore_()
