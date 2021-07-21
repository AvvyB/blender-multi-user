class SESSION_PT_network(bpy.types.Panel):
    bl_idname = "MULTIUSER_SETTINGS_PT_network"
    bl_label = "Network"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'MULTIUSER_SETTINGS_PT_network'

    @classmethod
    def poll(cls, context):
        return not session \
            or (session and session.state == 0)

    def draw_header(self, context):
        self.layout.label(text="", icon='LINKED')

    def draw(self, context):
        layout = self.layout

        runtime_settings = context.window_manager.session
        settings = get_preferences()

        # Create a simple row.
        row = layout.row()
        box = row.box()
        split = box.split(factor=0.35)
        split.label(text="Server")
        split = split.split(factor=0.3)
        split.label(text="Online")

        row = layout.row()
        layout.template_list("SESSION_UL_network",  "",  settings,
                             "server_preset_interface", context.window_manager,  "user_index")


class SESSION_UL_network(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        settings = get_preferences()
        server_name = '-'
        server_status = 'BLANK1'
        server_private = 'BLANK1'
        
        if not session:
            server_name = settings.server_name

            # Session with/without password
            if settings.server_password != None:
                server_private = 'LOCKED'
                split = layout.split(factor=0.35)
                split.label(text=server_name, icon=server_private)
            else:
                split = layout.split(factor=0.35)
                split.label(text=server_name)

            # Session status
            # if session online : vert else rouge
            from multi_user import icons
            server_status = icons.icons_col["session_status_offline"]
            split.label(icon=server_status)

class SESSION_UL_users(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        settings = get_preferences()
        is_local_user = item.username == settings.username
        ping = '-'
        frame_current = '-'
        scene_current = '-'
        mode_current = '-'
        mode_icon = 'BLANK1'
        status_icon = 'BLANK1'
        if session:
            user = session.online_users.get(item.username)
            if user:
                ping = str(user['latency'])
                metadata = user.get('metadata')
                if metadata and 'frame_current' in metadata:
                    frame_current = str(metadata.get('frame_current','-'))
                    scene_current = metadata.get('scene_current','-')
                    mode_current = metadata.get('mode_current','-')
                    if mode_current == "OBJECT" :
                        mode_icon = "OBJECT_DATAMODE"
                    elif mode_current == "EDIT_MESH" :
                        mode_icon = "EDITMODE_HLT"
                    elif mode_current == 'EDIT_CURVE':
                        mode_icon = "CURVE_DATA"
                    elif mode_current == 'EDIT_SURFACE':
                        mode_icon = "SURFACE_DATA"
                    elif mode_current == 'EDIT_TEXT':
                        mode_icon = "FILE_FONT"
                    elif mode_current == 'EDIT_ARMATURE':
                        mode_icon = "ARMATURE_DATA"
                    elif mode_current == 'EDIT_METABALL':
                        mode_icon = "META_BALL"
                    elif mode_current == 'EDIT_LATTICE':
                        mode_icon = "LATTICE_DATA"
                    elif mode_current == 'POSE':
                        mode_icon = "POSE_HLT"
                    elif mode_current == 'SCULPT':
                        mode_icon = "SCULPTMODE_HLT"
                    elif mode_current == 'PAINT_WEIGHT':
                        mode_icon = "WPAINT_HLT"
                    elif mode_current == 'PAINT_VERTEX':
                        mode_icon = "VPAINT_HLT"
                    elif mode_current == 'PAINT_TEXTURE':
                        mode_icon = "TPAINT_HLT"
                    elif mode_current == 'PARTICLE':
                        mode_icon = "PARTICLES"
                    elif mode_current == 'PAINT_GPENCIL' or mode_current =='EDIT_GPENCIL' or mode_current =='SCULPT_GPENCIL' or mode_current =='WEIGHT_GPENCIL' or mode_current =='VERTEX_GPENCIL':
                        mode_icon = "GREASEPENCIL"
                if user['admin']:
                    status_icon = 'FAKE_USER_ON'
        split = layout.split(factor=0.35)
        split.label(text=item.username, icon=status_icon)
        split = split.split(factor=0.3)
        split.label(icon=mode_icon)
        split.label(text=frame_current)
        split.label(text=scene_current)
        split.label(text=ping)