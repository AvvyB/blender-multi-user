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


import copy
import logging
import math

import bgl
import blf
import bpy
import gpu
import mathutils
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader

from . import utils

renderer = None

logger = logging.getLogger(__name__)


def view3d_find():
    """ Find the first 'VIEW_3D' windows found in areas

        :return: tuple(Area, Region, RegionView3D)
    """
    for area in bpy.data.window_managers[0].windows[0].screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    return area, region, rv3d
    return None, None, None


def refresh_3d_view():
    """ Refresh the viewport
    """
    area, region, rv3d = view3d_find()
    if area and region and rv3d:
        area.tag_redraw()

def refresh_sidebar_view():
    """ Refresh the blender sidebar
    """
    area, region, rv3d = view3d_find()

    area.regions[3].tag_redraw()

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

def get_default_bbox(obj, radius):
    coords = [
        (-radius, -radius, -radius), (+radius, -radius, -radius),
        (-radius, +radius, -radius), (+radius, +radius, -radius),
        (-radius, -radius, +radius), (+radius, -radius, +radius),
        (-radius, +radius, +radius), (+radius, +radius, +radius)]

    base = obj.matrix_world
    bbox_corners =  [base @ mathutils.Vector(corner) for corner in coords]

    return [(point.x, point.y, point.z)
                for point in bbox_corners]

def get_view_corners():
    area, region, rv3d = view3d_find()

    v1 = [0, 0, 0]
    v2 = [0, 0, 0]
    v3 = [0, 0, 0]
    v4 = [0, 0, 0]
    v5 = [0, 0, 0]
    v6 = [0, 0, 0]
    v7 = [0, 0, 0]

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

def get_bb_coords_from_obj(object, parent=None):
    base = object.matrix_world if parent is None else parent.matrix_world
    bbox_corners = [base @ mathutils.Vector(
                corner) for corner in object.bound_box]

    return [(point.x, point.y, point.z)
                for point in bbox_corners]


def get_view_matrix():
    area, region, rv3d = view3d_find()

    if area and region and rv3d:       
        return [list(v) for v in rv3d.view_matrix]

def update_presence(self, context):
    global renderer

    if 'renderer' in globals() and hasattr(renderer, 'run'):
        if self.enable_presence:
            renderer.run()
        else:
            renderer.stop()


def update_overlay_settings(self, context):
    global renderer

    if renderer and not self.presence_show_selected:
        renderer.flush_selection()
    if renderer and not self.presence_show_user:
        renderer.flush_users()


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
        self.flush_users()
        self.flush_selection()
        self.unregister_handlers()

        refresh_3d_view()

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

    def flush_selection(self, user=None):
        key_to_remove = []
        select_key = "{}_select".format(user) if user else "select"
        for k in self.d3d_items.keys():

            if select_key in k:
                key_to_remove.append(k)

        for k in key_to_remove:
            del self.d3d_items[k]

    def flush_users(self):
        key_to_remove = []
        for k in self.d3d_items.keys():
            if "select" not in k:
                key_to_remove.append(k)

        for k in key_to_remove:
            del self.d3d_items[k]

        self.d2d_items.clear()

    def draw_client_selection(self, client_id, client_color, client_selection):
        local_user = utils.get_preferences().username

        if local_user != client_id:
            self.flush_selection(client_id)

            for select_ob in client_selection:
                drawable_key = "{}_select_{}".format(client_id, select_ob)
               
                ob = utils.find_from_attr("uuid", select_ob, bpy.data.objects)
                if not ob:
                    return
            
                if ob.type == 'EMPTY':
                    # TODO: Child case
                    # Collection instance case
                    indices = (
                        (0, 1), (1, 2), (2, 3), (0, 3),
                        (4, 5), (5, 6), (6, 7), (4, 7),
                        (0, 4), (1, 5), (2, 6), (3, 7))
                    if ob.instance_collection:
                        for obj in ob.instance_collection.objects:
                            if obj.type == 'MESH':
                                self.append_3d_item(
                                    drawable_key,
                                    client_color,
                                    get_bb_coords_from_obj(obj, parent=ob),
                                    indices)
                    
                if ob.type in ['MESH','META']:
                    indices = (
                        (0, 1), (1, 2), (2, 3), (0, 3),
                        (4, 5), (5, 6), (6, 7), (4, 7),
                        (0, 4), (1, 5), (2, 6), (3, 7))
                        
                    self.append_3d_item(
                        drawable_key,
                        client_color,
                        get_bb_coords_from_obj(ob),
                        indices)
                else:
                    indices = (
                        (0, 1), (0, 2), (1, 3), (2, 3),
                        (4, 5), (4, 6), (5, 7), (6, 7),
                        (0, 4), (1, 5), (2, 6), (3, 7))

                    self.append_3d_item(
                        drawable_key,
                        client_color,
                        get_default_bbox(ob, ob.scale.x),
                        indices)
                        
    def append_3d_item(self,key,color, coords, indices):
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        color = color
        batch = batch_for_shader(
            shader, 'LINES', {"pos": coords}, indices=indices)

        self.d3d_items[key] = (shader, batch, color)

    def draw_client_camera(self, client_id, client_location, client_color):
        if client_location:
            local_user = utils.get_preferences().username

            if local_user != client_id:
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

                    self.d3d_items[client_id] = (shader, batch, color)
                    self.d2d_items[client_id] = (position[1], client_id, color)

                except Exception as e:
                    logger.error("Draw client exception {}".format(e))

    def draw3d_callback(self):
        bgl.glLineWidth(1.5)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)

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
