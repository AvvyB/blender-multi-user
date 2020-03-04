import logging

import bpy

from . import operators, presence, utils
from .libs.replication.replication.constants import FETCHED, RP_COMMON, STATE_INITIAL,STATE_QUITTING, STATE_ACTIVE, STATE_SYNCING, STATE_SRV_SYNC

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


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
        client =  operators.client
        if client and  client.state['STATE'] == STATE_ACTIVE:
            nodes = client.list(filter=self._type)

            for node in nodes:
                node_ref = client.get(uuid=node)

                if node_ref.state == FETCHED:
                    try:
                        client.apply(node)
                    except Exception as e:
                        logger.error(
                            "fail to apply {}: {}".format(node_ref.uuid, e))


class DynamicRightSelectTimer(Timer):
    def __init__(self, timout=.1):
        super().__init__(timout)
        self._last_selection = []
        self._user = None
        self._right_strategy = RP_COMMON

    def execute(self):
        session = operators.client
        settings = utils.get_preferences()

        if session and session.state['STATE'] == STATE_ACTIVE:
            # Find user
            if self._user is None:
                self._user = session.online_users.get(settings.username)

            if self._right_strategy is None:
                self._right_strategy = session.config[
                    'right_strategy']

            if self._user:
                current_selection = utils.get_selected_objects(
                    bpy.context.scene,
                    bpy.data.window_managers['WinMan'].windows[0].view_layer
                )
                if current_selection != self._last_selection:
                    if self._right_strategy == RP_COMMON:
                        obj_common = [
                            o for o in self._last_selection if o not in current_selection]
                        obj_ours = [
                            o for o in current_selection if o not in self._last_selection]

                        # change old selection right to common
                        for obj in obj_common:
                            node = session.get(uuid=obj)

                            if node and (node.owner == settings.username or node.owner == RP_COMMON):
                                recursive = True
                                if node.data and 'instance_type' in node.data.keys():
                                    recursive = node.data['instance_type'] != 'COLLECTION'
                                session.change_owner(
                                    node.uuid,
                                    RP_COMMON,
                                    recursive=recursive)

                        # change new selection to our
                        for obj in obj_ours:
                            node = session.get(uuid=obj)

                            if node and node.owner == RP_COMMON:
                                recursive = True
                                if node.data and 'instance_type' in node.data.keys():
                                    recursive = node.data['instance_type'] != 'COLLECTION'

                                session.change_owner(
                                    node.uuid,
                                    settings.username,
                                    recursive=recursive)
                            else:
                                return

                        self._last_selection = current_selection

                        user_metadata = {
                            'selected_objects': current_selection
                        }

                        session.update_user_metadata(user_metadata)
                        logger.info("Update selection")

                        # Fix deselection until right managment refactoring (with Roles concepts)
                        if len(current_selection) == 0 and self._right_strategy == RP_COMMON:
                            owned_keys = session.list(
                                filter_owner=settings.username)
                            for key in owned_keys:
                                node = session.get(uuid=key)

                                session.change_owner(
                                    key,
                                    RP_COMMON,
                                    recursive=recursive)

            for user, user_info in session.online_users.items():
                if user != settings.username:
                    metadata = user_info.get('metadata')

                    if 'selected_objects' in metadata:
                        # Update selectionnable objects
                        for obj in bpy.data.objects:
                            if obj.hide_select and obj.uuid not in metadata['selected_objects']:
                                obj.hide_select = False
                            elif not obj.hide_select and obj.uuid in metadata['selected_objects']:
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
            pass


class DrawClient(Draw):
    def execute(self):
        session = getattr(operators, 'client', None)
        renderer = getattr(presence, 'renderer', None)
        
        if session and renderer and session.state['STATE'] == STATE_ACTIVE:
            settings = bpy.context.window_manager.session
            users = session.online_users

            for user in users.values():
                metadata = user.get('metadata')

                if 'color' in metadata:
                    if settings.presence_show_selected and 'selected_objects' in metadata.keys():
                        renderer.draw_client_selection(
                            user['id'], metadata['color'], metadata['selected_objects'])
                    if settings.presence_show_user and 'view_corners' in metadata:
                        renderer.draw_client_camera(
                            user['id'], metadata['view_corners'], metadata['color'])


class ClientUpdate(Timer):
    def __init__(self, timout=.5):
        super().__init__(timout)
        self.handle_quit = False

    def execute(self):
        settings = utils.get_preferences()
        session = getattr(operators, 'client', None)
        renderer = getattr(presence, 'renderer', None)
       
        if session and renderer and session.state['STATE'] == STATE_ACTIVE:
            # Check if session has been closes prematurely
            if session.state['STATE'] == 0:
                bpy.ops.session.stop()

            local_user = operators.client.online_users.get(
                settings.username)
            if not local_user:
                return

            local_user_metadata = local_user.get('metadata')
            current_view_corners = presence.get_view_corners()

            if not local_user_metadata or 'color' not in local_user_metadata.keys():
                metadata = {
                    'view_corners': current_view_corners,
                    'view_matrix': presence.get_view_matrix(),
                    'color': (settings.client_color.r,
                              settings.client_color.g,
                              settings.client_color.b,
                              1),
                    'frame_current':bpy.context.scene.frame_current
                }
                session.update_user_metadata(metadata)
            elif current_view_corners != local_user_metadata['view_corners']:
                logger.info('update user metadata')
                local_user_metadata['view_corners'] = current_view_corners
                local_user_metadata['view_matrix'] = presence.get_view_matrix()
                session.update_user_metadata(local_user_metadata)

            # sync online users
            session_users = operators.client.online_users
            ui_users = bpy.context.window_manager.online_users

            for index, user in enumerate(ui_users):
                if user.username not in session_users.keys():
                    ui_users.remove(index)
                    
                    renderer.flush_selection()
                    renderer.flush_users()
                    
                    
                    break

            for user in session_users:
                if user not in ui_users:
                    new_key = ui_users.add()
                    new_key.name = user
                    new_key.username = user

            # TODO: event drivent 3d view refresh
            presence.refresh_3d_view()
        elif session.state['STATE'] == STATE_QUITTING:
            presence.refresh_3d_view()
            self.handle_quit = True
        elif session.state['STATE'] == STATE_INITIAL and self.handle_quit:
            self.handle_quit = False
            presence.refresh_3d_view()
            
            operators.unregister_delayables()
            
            presence.renderer.stop()
        # # ui update
        elif session:
            presence.refresh_3d_view()