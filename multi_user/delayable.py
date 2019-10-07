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
                    except Exception:
                        logger.error("fail to apply")


class DynamicRightSelectTimer(Timer):
    def __init__(self, timout=.1):
        super().__init__(timout)
        self.last_selection = []

    def execute(self):
        if operators.client:
            users = operators.client.list(filter=BlUser)

            for user in users:
                user_ref = operators.client.get(uuid=user)
                settings = bpy.context.window_manager.session

                # Local user
                if user_ref.pointer:
                    current_selection = utils.get_selected_objects(
                        bpy.context.scene)
                    if current_selection != self.last_selection:
                        right_strategy = operators.client.get_config()[
                            'right_strategy']
                        if right_strategy == RP_COMMON:
                            obj_common = [
                                o for o in self.last_selection if o not in current_selection]
                            obj_ours = [
                                o for o in current_selection if o not in self.last_selection]

                            # change new selection to our
                            for obj in obj_ours:
                                node = operators.client.get(
                                    reference=bpy.data.objects[obj])
                                if node and node.owner == RP_COMMON:
                                    operators.client.change_owner(
                                        node.uuid, settings.username)
                                else:
                                    return

                            self.last_selection = current_selection
                            user_ref.pointer.update_selected_objects(
                                bpy.context)
                            user_ref.update()

                            # change old selection right to common
                            for obj in obj_common:
                                _object = bpy.data.objects.get(obj)

                                node = operators.client.get(reference=_object)
                                if node and (node.owner == settings.username or node.owner == RP_COMMON):
                                    operators.client.change_owner(
                                        node.uuid, RP_COMMON)
                else:
                    for obj in bpy.data.objects:
                        if obj.hide_select and obj.name not in user_ref.data['selected_objects']:
                            obj.hide_select = False
                        elif not obj.hide_select and obj.name in user_ref.data['selected_objects']:
                            obj.hide_select = True

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
        repo = operators.client
        if repo and presence.renderer:
            settings = bpy.context.window_manager.session
            client_list = [key for key in repo.list(filter=BlUser) if
                           key != settings.user_uuid]

            for cli in client_list:
                cli_ref = repo.get(uuid=cli)

                if settings.presence_show_selected:
                    presence.renderer.draw_client_selection(
                        cli_ref.data['name'], cli_ref.data['color'], cli_ref.data['selected_objects'])
                if settings.presence_show_user:
                    presence.renderer.draw_client_camera(
                        cli_ref.data['name'], cli_ref.data['location'], cli_ref.data['color'])


class ClientUpdate(Timer):
    def __init__(self, timout=1, client_uuid=None):
        assert(client_uuid)
        self._client_uuid = client_uuid
        super().__init__(timout)

    def execute(self):
        if self._client_uuid and operators.client:
            client = operators.client.get(uuid=self._client_uuid)

            if client:
                client.pointer.update_location()
