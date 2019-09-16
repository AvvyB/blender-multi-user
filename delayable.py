import bpy
import logging

from . import operators, utils, presence
from .bl_types.bl_user import BlUser
from .libs import debug
from .libs.replication.replication.constants import FETCHED

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
                client.pointer.update_selected_objects(bpy.context)
