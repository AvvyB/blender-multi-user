import bpy
import bgl
import blf
import gpu
import mathutils
import copy
import logging
import math


from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader

from . import utils
from .libs import debug
# from .bl_types.bl_user import BlUser
# from .delayable import Draw

global renderer

logger = logging.getLogger(__name__)

def view3d_find():
    for area in bpy.data.window_managers[0].windows[0].screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    return area, region, rv3d

    return None, None, None

def refresh_3d_view():
    area, region, rv3d = view3d_find()

    area.tag_redraw()

def get_target(region, rv3d, coord):
    target = [0, 0, 0]

    if coord and region and rv3d:
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        target = ray_origin + view_vector

    return [target.x, target.y, target.z]


def get_target_far(region, rv3d, coord, distance):
    target = [0, 0, 0]

    if coord and region and rv3d:
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        target = ray_origin + view_vector * distance

    return [target.x, target.y, target.z]


def get_client_cam_points():
    area, region, rv3d = view3d_find()

    v1 = [0, 0, 0]
    v2 = [0, 0, 0]
    v3 = [0, 0, 0]
    v4 = [0, 0, 0]
    v5 = [0, 0, 0]
    v6 = [0, 0, 0]

    if area and region and rv3d:
        width = region.width
        height = region.height

        v1 = get_target(region, rv3d, (0, 0))
        v3 = get_target(region, rv3d, (0, height))
        v2 = get_target(region, rv3d, (width, height))
        v4 = get_target(region, rv3d, (width, 0))

        v5 = get_target(region, rv3d, (width/2, height/2))
        v6 = list(rv3d.view_location)
        v7 = get_target_far(region, rv3d, (width/2, height/2), -.8)

    coords = [v1, v2, v3, v4, v5, v6, v7]

    return coords


def get_client_2d(coords):
    area, region, rv3d = view3d_find()
    if area and region and rv3d:
        return view3d_utils.location_3d_to_region_2d(region, rv3d, coords)
    else:
        return (0, 0)


class User():
    def __init__(self, username=None, color=(0, 0, 0, 1)):
        self.is_dirty = False
        self.name = username
        self.color = color
        self.location = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
        self.selected_objects = []

    def update_location(self):
        current_coords = get_client_cam_points()
        area, region, rv3d = view3d_find()

        current_coords = get_client_cam_points()
        if current_coords:
            self.location = list(current_coords)

    def update_selected_objects(self, context):
        self.selected_objects = utils.get_selected_objects(context.scene)


class DrawFactory(object):

    def __init__(self):
        self.d3d_items = {}
        self.d2d_items = {}
        self.draw3d_handle = None
        self.draw2d_handle = None
        self.draw_event = None
        self.coords = None
        self.active_object = None

    def run(self):
        self.register_handlers()

    def stop(self):
        self.unregister_handlers()

    def register_handlers(self):
        self.draw3d_handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw3d_callback, (), 'WINDOW', 'POST_VIEW')
        self.draw2d_handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw2d_callback, (), 'WINDOW', 'POST_PIXEL')

    def unregister_handlers(self):
        if self.draw2d_handle:
            bpy.types.SpaceView3D.draw_handler_remove(
                self.draw2d_handle, "WINDOW")
            self.draw2d_handle = None

        if self.draw3d_handle:
            bpy.types.SpaceView3D.draw_handler_remove(
                self.draw3d_handle, "WINDOW")
            self.draw3d_handle = None

        self.d3d_items.clear()
        self.d2d_items.clear()

    def draw_client_selection(self, client_uuid, client_color, client_selection):
        local_username = bpy.context.window_manager.session.username
        
        key_to_remove = []
        for k in self.d3d_items.keys():
            if "{}_select".format(client_uuid) in k:
                key_to_remove.append(k)

        for k in key_to_remove:
            del self.d3d_items[k]

        if client_selection:
            
            for select_ob in client_selection:
                drawable_key = "{}_select_{}".format(client_uuid, select_ob)
                indices = (
                    (0, 1), (1, 2), (2, 3), (0, 3),
                    (4, 5), (5, 6), (6, 7), (4, 7),
                    (0, 4), (1, 5), (2, 6), (3, 7)
                )

                if select_ob in bpy.data.objects.keys():
                    ob = bpy.data.objects[select_ob]
                else:
                    return

                bbox_corners = [ob.matrix_world @ mathutils.Vector(
                    corner) for corner in ob.bound_box]

                coords = [(point.x, point.y, point.z)
                            for point in bbox_corners]
                shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
                color = client_color
                batch = batch_for_shader(
                    shader, 'LINES', {"pos": coords}, indices=indices)
               

                self.d3d_items[drawable_key] = (shader, batch, color)
                
    def draw_client_camera(self, client_uuid, client_location, client_color):
        if client_location:
            local_username = bpy.context.window_manager.session.username

            try:
                indices = (
                    (1, 3), (2, 1), (3, 0),
                    (2, 0), (4, 5), (1, 6),
                    (2, 6), (3, 6), (0, 6)
                )

                shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
                position = [tuple(coord) for coord in client_location]
                color = client_color

                batch = batch_for_shader(
                    shader, 'LINES', {"pos": position}, indices=indices)

                self.d3d_items[client_uuid] = (shader, batch, color)
                self.d2d_items[client_uuid] = (position[1], client_uuid, color)

            except Exception as e:
                logger.error("Draw client exception {}".format(e))

    def draw3d_callback(self):
        bgl.glLineWidth(1.5)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        try:
            for shader, batch, color in self.d3d_items.values():
                shader.bind()
                shader.uniform_float("color", color)
                batch.draw(shader)
        except Exception:
            logger.error("3D Exception")

    def draw2d_callback(self):
        for position, font, color in self.d2d_items.values():
            try:
                coords = get_client_2d(position)

                if coords:
                    blf.position(0, coords[0], coords[1]+10, 0)
                    blf.size(0, 16, 72)
                    blf.color(0, color[0], color[1], color[2], color[3])
                    blf.draw(0,  font)

            except Exception:
                logger.error("2D EXCEPTION")


def register():
    global renderer
    renderer = DrawFactory()


def unregister():
    global renderer
    renderer.unregister_handlers()

    del renderer
