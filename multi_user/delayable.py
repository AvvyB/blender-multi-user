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

import logging

import bpy

from . import operators, presence, utils
from .libs.replication.replication.constants import FETCHED, RP_COMMON, STATE_INITIAL,STATE_QUITTING, STATE_ACTIVE, STATE_SYNCING, STATE_SRV_SYNC


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
                        logging.error(f"Fail to apply {node_ref.uuid}: {e}")


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
                        logging.debug("Update selection")

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
        prefs = utils.get_preferences()
        
        if session and renderer and session.state['STATE'] == STATE_ACTIVE:
            settings = bpy.context.window_manager.session
            users = session.online_users

            # Update users 
            for user in users.values():
                metadata = user.get('metadata')
                color = metadata.get('color')
                scene_current = metadata.get('scene_current')
                user_showable = scene_current == bpy.context.scene.name or settings.presence_show_far_user
                if color and scene_current and user_showable:
                    if settings.presence_show_selected and 'selected_objects' in metadata.keys():
                        renderer.draw_client_selection(
                            user['id'], color, metadata['selected_objects'])
                    if settings.presence_show_user and 'view_corners' in metadata:
                        renderer.draw_client_camera(
                            user['id'], metadata['view_corners'], color)
                if not user_showable:
                    # TODO: remove this when user event drivent update will be 
                    # ready
                    renderer.flush_selection()
                    renderer.flush_users()


class ClientUpdate(Timer):
    def __init__(self, timout=.016):
        super().__init__(timout)
        self.handle_quit = False
        self.users_metadata = {}

    def execute(self):
        settings = utils.get_preferences()
        session = getattr(operators, 'client', None)
        renderer = getattr(presence, 'renderer', None)
       
        if session and renderer:
            if session.state['STATE'] == STATE_ACTIVE:
                # Check if session has been closes prematurely
                if session.state['STATE'] == 0:
                    bpy.ops.session.stop()

                local_user =  operators.client.online_users.get(settings.username)
                
                if not local_user:
                    return
                else:
                    for username, user_data in operators.client.online_users.items():
                        if username != settings.username:
                            cached_user_data = self.users_metadata.get(username)
                            new_user_data = operators.client.online_users[username]['metadata']
                            
                            if cached_user_data is None:
                                self.users_metadata[username] = user_data['metadata']
                            elif 'view_matrix' in cached_user_data and 'view_matrix' in new_user_data and cached_user_data['view_matrix'] != new_user_data['view_matrix']:
                                presence.refresh_3d_view()
                                self.users_metadata[username] = user_data['metadata']
                                break
                            else:
                                self.users_metadata[username] = user_data['metadata']

                local_user_metadata = local_user.get('metadata')
                scene_current = bpy.context.scene.name
                local_user =  session.online_users.get(settings.username)
                current_view_corners = presence.get_view_corners()
                    
                # Init client metadata
                if not local_user_metadata or 'color' not in local_user_metadata.keys():
                    metadata = {
                        'view_corners': presence.get_view_matrix(),
                        'view_matrix': presence.get_view_matrix(),
                        'color': (settings.client_color.r,
                                settings.client_color.g,
                                settings.client_color.b,
                                1),
                        'frame_current':bpy.context.scene.frame_current,
                        'scene_current': scene_current
                    }
                    session.update_user_metadata(metadata)

                # Update client representation
                # Update client current scene
                elif scene_current != local_user_metadata['scene_current']:
                    local_user_metadata['scene_current'] = scene_current
                    session.update_user_metadata(local_user_metadata)            
                elif 'view_corners' in local_user_metadata  and current_view_corners != local_user_metadata['view_corners']:
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
            elif session.state['STATE'] == STATE_QUITTING:
                presence.refresh_sidebar_view()
                self.handle_quit = True
            elif session.state['STATE'] == STATE_INITIAL and self.handle_quit:
                self.handle_quit = False
                presence.refresh_sidebar_view()
                
                operators.unregister_delayables()
                
                presence.renderer.stop()
            
            presence.refresh_sidebar_view()