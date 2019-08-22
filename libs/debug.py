import bpy
import bgl
import gpu
from gpu_extras.batch import batch_for_shader
import numpy


DEFAULT_COORDS = [(0.0, 0.0, 0.0)]
DEFAULT_INDICES = [(0)]


def refresh_viewport():
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)


class Drawable():
    """Drawable base class in charge to hanfle the drawing pipline.

    :param coords: list of vertices
    :type coords: list of tuples. ex: [(x,y,z),...]
    :param indices: list of vertices index to structure geometry
    :type indices: list of tuples.
    :param location: suited location in world space.
    :type location: tuple, (x,y,z)
    :param mode: primitive drawing mode.
    :type mode: string in ['POINTS','LINES','TRIS'], default: "POINTS".
    :param color: primitive color
    :type color: tuple, (r,g,b,a)
    :param duration: lifetime of the primitive in seconds
    :type duration: float
    """

    def __init__(self, coords=DEFAULT_COORDS, indices=DEFAULT_INDICES, location=(0.0, 0.0, 0.0), mode='POINTS', color=(1, 0, 0, 1), duration=0):
        self._duration = duration
        self._color = color
        self._coord = [tuple(numpy.add(c,location)) for c in coords]
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.batch = batch_for_shader(
            self.shader, mode, {"pos": self._coord}, indices=indices)

        # Bind the drawing function
        self._handler = bpy.types.SpaceView3D.draw_handler_add(
            self.draw, (), 'WINDOW', 'POST_VIEW')
        # Bind the callback
        if duration:
            self._timer = bpy.app.timers.register(
                self.clear, first_interval=duration)

    def draw(self):
        self.shader.bind()
        self.shader.uniform_float("color", self._color)
        self.batch.draw(self.shader)

    def clear(self):
        """Remove the drawable object from the viewport
        """
        bpy.types.SpaceView3D.draw_handler_remove(self._handler, 'WINDOW')


def draw_point(location=(0, 0, 0), color=(1, 0, 0, 1), duration=1):
    """Draw a point

    :param location: suited location in world space.
    :type location: tuple, (x,y,z)
    :param color: primitive color
    :type color: tuple, (r,g,b,a)
    :param duration: lifetime of the primitive in seconds
    :type duration: float
    """
    return Drawable(location=location, color=color, duration=duration)


def draw_line(a=(0, 0, 0), b=(0, 1, 0), color=(1, 0, 0, 1), duration=1):
    """ Draw a line from a given point A to the point B.

    :param a: point A location in world space.
    :type a: tuple, (x,y,z)
    :param b: point B location in world space.
    :type b: tuple, (x,y,z)
    :param color: primitive color
    :type color: tuple, (r,g,b,a)
    :param duration: lifetime of the primitive in seconds
    :type duration: float
    """
    return Drawable(coords=[a, b], indices=[(0, 1)], mode='LINES', color=color, duration=duration)


def draw_cube(radius=1, location=(0, 0, 0), color=(1, 0, 0, 1), duration=1):
    """ Draw a cube.

    :param radius: size of the cube.
    :type radius: float
    :param location: suited location in world space.
    :type location: tuple, (x,y,z)
    :param color: primitive color
    :type color: tuple, (r,g,b,a)
    :param duration: lifetime of the primitive in seconds
    :type duration: float
    """
    coords = (
        (-radius, -radius, -radius), (+radius, -radius, -radius),
        (-radius, +radius, -radius), (+radius, +radius, -radius),
        (-radius, -radius, +radius), (+radius, -radius, +radius),
        (-radius, +radius, +radius), (+radius, +radius, +radius))

    indices = (
        (0, 1), (0, 2), (1, 3), (2, 3),
        (4, 5), (4, 6), (5, 7), (6, 7),
        (0, 4), (1, 5), (2, 6), (3, 7))

    return Drawable(coords=coords, mode='LINES', indices=indices, location=location, color=color, duration=duration)

def draw_custom(coords=DEFAULT_COORDS, indices=DEFAULT_INDICES, mode='LINES',location=(0, 0, 0), color=(1, 0, 0, 1), duration=1):
    """ Draw a user defined polygon shape.

    :param coords: list of vertices
    :type coords: list of tuples. ex: [(x,y,z),...]
    :param indices: list of vertices index to structure geometry
    :type indices: list of tuples.
    :param location: suited location in 
    :param color: primitive color
    :type color: tuple, (r,g,b,a)
    :param duration: lifetime of the primitive in seconds
    :type duration: float
    """
    return Drawable(coords=coords, indices=indices, mode=mode, location=location, color=color, duration=duration)
