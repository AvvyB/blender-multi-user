import bpy
import logging

from . import operators, utils, presence
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

    def register(self):
        """Register the timer into the blender timer system
        """
        bpy.app.timers.register(self.execute)

    def execute(self):
        """Main timer loop
        """
        return self._timeout

    def unregister(self):
        """Unnegister the timer of the blender timer system
        """
        try:
            bpy.app.timers.unregister(self.execute)
        except:
            logger.error("timer already unregistered")


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
                    operators.client.apply(uuid=node)

        return self._timeout

class DynamicRightSelectTimer(Timer):
    def __init__(self, timout=1):
        super().__init__(timout)
        self.last_selection=[]

    def execute(self):
        if operators.client:
            users = operators.client.list(filter=BlUser)

            for user in users:
                user_ref = operators.client.get(uuid=user)
                settings = bpy.context.window_manager.session
                
                if user_ref.buffer['name'] != settings.username:
                    for obj in bpy.data.objects:
                        obj.hide_select = obj.name in user_ref.buffer['selected_objects']
                elif user_ref.pointer:
                    current_selection = utils.get_selected_objects(bpy.context.scene)
                    if current_selection != self.last_selection:
                        user_ref.pointer.update_selected_objects(bpy.context)

                        if operators.client.get_config()['right_strategy'] == 'COMMON':
                            obj_common = [o for o in self.last_selection if o not in current_selection]
                            obj_ours = [o for o in current_selection if o not in self.last_selection]

                            for obj in obj_common:
                                node = operators.client.get(reference=bpy.data.objects[obj])
                                if node:
                                    node.owner =  settings.username
                                    operators.client.change_owner(node.uuid, RP_COMMON)

                            # update our rights
                            for obj in obj_ours:
                                node = operators.client.get(reference=bpy.data.objects[obj])
                                if node:
                                    node.owner =  settings.username
                                    operators.client.change_owner(node.uuid, settings.username)
                        self.last_selection = current_selection
        return self._timeout

# class CheckNewTimer(Timer):

class RedrawTimer(Timer):
    def __init__(self, timout=1, target_type=None):
        self._type = target_type
        super().__init__(timout)

    def execute(self):
        if presence.renderer:
            presence.refresh_3d_view()

        return self._timeout

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


class ClientUpdate(Draw):
    def __init__(self, client_uuid=None):
        assert(client_uuid)
        self._client_uuid = client_uuid
        super().__init__()

    def execute(self):
        if self._client_uuid and operators.client:
            client = operators.client.get(uuid=self._client_uuid)

            if client:
                client.pointer.update_location()
