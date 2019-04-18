import bpy
import bgl
import blf
import gpu
import mathutils

from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader


def view3d_find():
    for area in bpy.data.window_managers[0].windows[0].screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    return area, region, rv3d

    return None, None, None


def get_target(region, rv3d, coord):
    target = [0, 0, 0]

    if coord and region and rv3d:
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        target = ray_origin + view_vector

    return [target.x, target.y, target.z]


def get_client_view_rect():
    area, region, rv3d = view3d_find()

    v1 = [0, 0, 0]
    v2 = [0, 0, 0]
    v3 = [0, 0, 0]
    v4 = [0, 0, 0]

    if area and region and rv3d:
        width = region.width
        height = region.height

        v1 = get_target(region, rv3d, (0, 0))
        v3 = get_target(region, rv3d, (0, height))
        v2 = get_target(region, rv3d, (width, height))
        v4 = get_target(region, rv3d, (width, 0))

    coords = [v1, v2, v3, v4]
    indices = (
        (1, 3), (2, 1), (3, 0), (2, 0)
    )

    return coords


def get_client_2d(coords):
    area, region, rv3d = view3d_find()
    if area and region and rv3d:
        return view3d_utils.location_3d_to_region_2d(region, rv3d, coords)
    else:
        return (0, 0)


class HUD(object):

    def __init__(self, client_instance=None):
        self.d3d_items = {}
        self.d2d_items = {}
        self.draw3d_handle = None
        self.draw2d_handle = None
        self.draw_event = None
        self.coords = None
        self.active_object = None

        if client_instance:
            self.client = client_instance

            self.draw_clients()
            self.register_handlers()

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

    def draw_selected_object(self):
        clients = self.client.get("Client")

        for client in clients:
            name = client[0].split('/')[1]
            local_username = bpy.context.scene.session_settings.username

            if name != local_username:
                if client[1]['active_objects']:
                    for select_ob in client[1]['active_objects']:
                        indices = (
                            (0, 1), (1, 2), (2, 3), (0, 3),
                            (4, 5), (5, 6), (6, 7), (4, 7),
                            (0, 4), (1, 5), (2, 6), (3, 7)
                        )

                        if select_ob in bpy.data.objects.keys():
                            ob = bpy.data.objects[select_ob]
                        else:
                            return

                        bbox_corners = [ob.matrix_world @ mathutils.Vector(corner) for corner in ob.bound_box]

                        coords = [(point.x, point.y, point.z)
                                for point in bbox_corners]

                        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

                        color = client[1]['color']

                        batch = batch_for_shader(
                            shader, 'LINES', {"pos": coords}, indices=indices)

                        self.d3d_items["{}/{}".format(client[0],
                                                    select_ob)] = (shader, batch, color)
                else:
                    self.d3d_items.clear()
    def draw_clients(self):
        clients = self.client.get("Client")

        for client in clients:
            name = client[0].split('/')[1]
            local_username = bpy.context.scene.session_settings.username

            if name != local_username:
                try:
                    indices = (
                        (1, 3), (2, 1), (3, 0), (2, 0)
                    )

                    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
                    position = client[1]['location']
                    color = client[1]['color']

                    batch = batch_for_shader(
                        shader, 'LINES', {"pos": position}, indices=indices)

                    self.d3d_items[client[0]] = (shader, batch, color)
                    self.d2d_items[client[0]] = (position[1], name, color)

                except Exception as e:
                    print("Draw client exception {}".format(e))

    def draw3d_callback(self):
        bgl.glLineWidth(3)
        try:
            for shader, batch, color in self.d3d_items.values():
                shader.bind()
                shader.uniform_float("color", color)
                batch.draw(shader)
        except Exception as e:
            print("3D Exception")

    def draw2d_callback(self):
        for position, font, color in self.d2d_items.values():
            try:
                coords = get_client_2d(position)

                if coords:
                    blf.position(0, coords[0], coords[1]+10, 0)
                    blf.size(0, 10, 72)
                    blf.color(0, color[0], color[1], color[2], color[3])
                    blf.draw(0,  font)

            except Exception as e:
                print("2D EXCEPTION")

    def draw(self):
        if self.client:
            # Draw clients
            self.draw_clients()
            self.draw_selected_object()
