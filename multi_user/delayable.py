import logging

import bpy

from . import operators, presence, utils
from .bl_types.bl_user import BlUser
from .libs.replication.replication.constants import FETCHED, RP_COMMON

logger = logging.getLogger(__name__)


class Delayable():
    """Delayable task interface
    """

    def register(self):
        raise NotImplementedError

    def execute(self):
        raise NotImplementedError

    def unregister(self):
        raise NotImplementedError


class Timer(Delayable):
    """Timer binder interface for blender

    Run a bpy.app.Timer in the background looping at the given rate
    """

    def __init__(self, duration=1):
        self._timeout = duration
        self._running = True

    def register(self):
        """Register the timer into the blender timer system
        """
        bpy.app.timers.register(self.main)

    def main(self):
        self.execute()

        if self._running:
            return self._timeout

    def execute(self):
        """Main timer loop
        """
        raise NotImplementedError

    def unregister(self):
        """Unnegister the timer of the blender timer system
        """
        if bpy.app.timers.is_registered(self.main):
            bpy.app.timers.unregister(self.main)

        self._running = False


class ApplyTimer(Timer):
    def __init__(self, timout=1, target_type=None):
        self._type = target_type
        super().__init__(timout)

    def execute(self):
        if operators.client:
            nodes = operators.client.list(filter=self._type)

            for node in nodes:
                node_ref = operators.client.get(uuid=node)

                if node_ref.state == FETCHED:
                    try:
                        operators.client.apply(node)
                    except Exception as e:
                        logger.error(
                            "fail to apply {}: {}".format(node_ref.uuid, e))


class DynamicRightSelectTimer(Timer):
    def __init__(self, timout=.1):
        super().__init__(timout)
        self._last_selection = []
        self._user = None
        self._user_node = None
        self._right_strategy = RP_COMMON

    def execute(self):
        repo = operators.client
        if repo:
            settings = bpy.context.window_manager.session

            # Find user
            if self._user is None:
                users = repo.list(filter=BlUser)

                for user in users:
                    user_node = repo.get(uuid=user)
                    if user_node.pointer:
                        self._user = user_node.pointer
                        self._user_node = user_node

            if self._right_strategy is None:
                self._right_strategy = repo.get_config()[
                    'right_strategy']

            if self._user:
                current_selection = utils.get_selected_objects(
                    bpy.context.scene)
                if current_selection != self._last_selection:
                    if self._right_strategy == RP_COMMON:
                        obj_common = [
                            o for o in self._last_selection if o not in current_selection]
                        obj_ours = [
                            o for o in current_selection if o not in self._last_selection]

                        # change old selection right to common
                        for obj in obj_common:
                            node = repo.get(uuid=obj)

                            if node and (node.owner == settings.username or node.owner == RP_COMMON):
                                recursive = True
                                if node.data and 'instance_type' in node.data.keys():
                                    recursive = node.data['instance_type'] != 'COLLECTION'
                                repo.change_owner(
                                    node.uuid,
                                    RP_COMMON,
                                    recursive=recursive)

                        # change new selection to our
                        for obj in obj_ours:
                            node = repo.get(uuid=obj)

                            if node and node.owner == RP_COMMON:
                                recursive = True
                                if node.data and 'instance_type' in node.data.keys():
                                    recursive = node.data['instance_type'] != 'COLLECTION'

                                repo.change_owner(
                                    node.uuid,
                                    settings.username,
                                    recursive=recursive)
                            else:
                                return

                        self._last_selection = current_selection
                        self._user.update_selected_objects(
                            bpy.context)
                        repo.push(self._user_node.uuid)

                        # Fix deselection until right managment refactoring (with Roles concepts)
                        if len(current_selection) == 0 and self._right_strategy == RP_COMMON:
                            owned_keys = repo.list(
                                filter_owner=settings.username)
                            for key in owned_keys:
                                node = repo.get(uuid=key)
                                if not isinstance(node, BlUser):
                                    repo.change_owner(
                                        key,
                                        RP_COMMON,
                                        recursive=recursive)


class Draw(Delayable):
    def __init__(self):
        self._handler = None

    def register(self):
        self._handler = bpy.types.SpaceView3D.draw_handler_add(
            self.execute, (), 'WINDOW', 'POST_VIEW')

    def execute(self):
        raise NotImplementedError()

    def unregister(self):
        try:
            bpy.types.SpaceView3D.draw_handler_remove(
                self._handler, "WINDOW")
        except:
            logger.error("draw already unregistered")


class DrawClient(Draw):
    def execute(self):
        session = operators.client
        if session and presence.renderer:
            settings = bpy.context.window_manager.session
            users = session.online_users

            for user in users.values():
                metadata = user.get('metadata')

                    # if settings.presence_show_selected:
                    #     presence.renderer.draw_client_selection(
                    #         cli_ref.data['name'], cli_ref.data['color'], cli_ref.data['selected_objects'])
                if settings.presence_show_user:
                    presence.renderer.draw_client_camera(
                        user['id'], metadata['view_corners'], metadata['color'])


class ClientUpdate(Timer):
    def __init__(self, timout=1, client_uuid=None):
        assert(client_uuid)
        self._client_uuid = client_uuid
        super().__init__(timout)

    def execute(self):
        settings = bpy.context.window_manager.session
        session_info = bpy.context.window_manager.session
        session = operators.client
        if self._client_uuid and operators.client:
            client = operators.client.get(uuid=self._client_uuid)
            local_user = operators.client.online_users[session_info.username]

            metadata = {
                'view_corners': presence.get_view_corners(),
                'view_matrix': presence.get_view_matrix(),
                'color': (settings.client_color.r,
                          settings.client_color.g,
                          settings.client_color.b,
                          1),
                'selected_objects':utils.get_selected_objects(bpy.context.scene)
            }

            session.update_user_metadata(metadata)

            logger.info("{}".format(local_user))
            if client:
                client.pointer.update_location()

            # sync online users
            session_users = operators.client.online_users
            ui_users = bpy.context.window_manager.online_users

            for index, user in enumerate(ui_users):
                if user.username not in session_users.keys():
                    ui_users.remove(index)
                    bpy.context.window_manager.session.presence_show_user = False
                    bpy.context.window_manager.session.presence_show_user = True
                    presence.refresh_3d_view()
                    break

            for user in session_users:
                if user not in ui_users:
                    new_key = ui_users.add()
                    new_key.name = user
                    new_key.username = user
