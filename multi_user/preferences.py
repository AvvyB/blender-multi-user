import logging
import bpy

from . import utils, bl_types, environment

logger = logging.getLogger(__name__)

class ReplicatedDatablock(bpy.types.PropertyGroup):
    type_name: bpy.props.StringProperty()
    bl_name: bpy.props.StringProperty()
    bl_delay_refresh: bpy.props.FloatProperty()
    bl_delay_apply: bpy.props.FloatProperty()
    use_as_filter: bpy.props.BoolProperty(default=True)
    auto_push: bpy.props.BoolProperty(default=True)
    icon: bpy.props.StringProperty()

class SessionPrefs(bpy.types.AddonPreferences):
    bl_idname  = __package__

    ip: bpy.props.StringProperty(
        name="ip",
        description='Distant host ip',
        default="127.0.0.1")
    username: bpy.props.StringProperty(
        name="Username",
        default="user_{}".format(utils.random_string_digits())
    )
    client_color: bpy.props.FloatVectorProperty(
        name="client_instance_color",
        subtype='COLOR',
        default=utils.randomColor())
    port: bpy.props.IntProperty(
        name="port",
        description='Distant host port',
        default=5555
        )
    supported_datablocks: bpy.props.CollectionProperty(
        type=ReplicatedDatablock,
        )
    ipc_port: bpy.props.IntProperty(
        name="ipc_port",
        description='internal ttl port(only usefull for multiple local instances)',
        default=5561
        )
    start_empty: bpy.props.BoolProperty(
        name="start_empty",
        default=False
        )
    right_strategy: bpy.props.EnumProperty(
        name='right_strategy',
        description='right strategy',
        items={
            ('STRICT', 'strict', 'strict right repartition'),
            ('COMMON', 'common', 'relaxed right repartition')},
        default='COMMON')
    cache_directory: bpy.props.StringProperty(
        name="cache directory",
        subtype="DIR_PATH",
        default=environment.DEFAULT_CACHE_DIR)
    # for UI
    # category: bpy.props.EnumProperty(
    #     name="Category",
    #     description="Preferences Category",
    #     items=[
    #         ('INFO', "Information", "Information about this add-on"),
    #         ('CONFIG', "Configuration", "Configuration about this add-on"),
    #         ('UPDATE', "Update", "Update this add-on"),
    #     ],
    #     default='INFO'
    # )
    conf_session_identity_expanded: bpy.props.BoolProperty(
        name="Identity",
        description="Identity",
        default=True
    )
    conf_session_net_expanded: bpy.props.BoolProperty(
        name="Net",
        description="net",
        default=True
    )
    conf_session_hosting_expanded: bpy.props.BoolProperty(
        name="Rights",
        description="Rights",
        default=False
    )
    conf_session_timing_expanded: bpy.props.BoolProperty(
        name="timings",
        description="timings",
        default=False
    )
    conf_session_cache_expanded: bpy.props.BoolProperty(
        name="Cache",
        description="cache",
        default=False
    )


    def draw(self, context):
        layout = self.layout

        # layout.row().prop(self, "category", expand=True)

        # if self.category == 'INFO':
        #     layout.separator()
        #     layout.label(text="Enable real-time collaborative workflow inside blender")
        # if self.category == 'CONFIG':
        grid = layout.column()
        
        # USER INFORMATIONS
        box = grid.box()
        box.prop(
            self, "conf_session_identity_expanded", text="User informations",
            icon='DISCLOSURE_TRI_DOWN' if self.conf_session_identity_expanded
            else 'DISCLOSURE_TRI_RIGHT', emboss=False)
        if self.conf_session_identity_expanded:
            box.row().prop(self, "username", text="name")
            box.row().prop(self, "client_color", text="color")

        # NETWORK SETTINGS
        box = grid.box()
        box.prop(
            self, "conf_session_net_expanded", text="Netorking",
            icon='DISCLOSURE_TRI_DOWN' if self.conf_session_net_expanded
            else 'DISCLOSURE_TRI_RIGHT', emboss=False)

        if self.conf_session_net_expanded:
            box.row().prop(self, "ip", text="Address")
            row = box.row()
            row.label(text="Port:")
            row.prop(self, "port", text="Address")
            row = box.row()
            row.label(text="Start with an empty scene:")
            row.prop(self, "start_empty", text="")

            table = box.box()
            table.row().prop(
                self, "conf_session_timing_expanded", text="Refresh rates",
                icon='DISCLOSURE_TRI_DOWN' if self.conf_session_timing_expanded
                else 'DISCLOSURE_TRI_RIGHT', emboss=False)
            
            if self.conf_session_timing_expanded:
                line = table.row()
                line.label(text=" ")
                line.separator()
                line.label(text="refresh (sec)")
                line.label(text="apply (sec)")

                for item in self.supported_datablocks:
                    line =  table.row(align=True)
                    line.label(text="", icon=item.icon)
                    line.prop(item, "bl_delay_refresh", text="")
                    line.prop(item, "bl_delay_apply", text="")
        # HOST SETTINGS
        box = grid.box()
        box.prop(
            self, "conf_session_hosting_expanded", text="Hosting",
            icon='DISCLOSURE_TRI_DOWN' if self.conf_session_hosting_expanded
            else 'DISCLOSURE_TRI_RIGHT', emboss=False)
        if self.conf_session_hosting_expanded:
            box.row().prop(self, "right_strategy", text="Right model")
            row = box.row()
            row.label(text="Start with an empty scene:")
            row.prop(self, "start_empty", text="")
        
        # CACHE SETTINGS
        box = grid.box()
        box.prop(
            self, "conf_session_cache_expanded", text="Cache",
            icon='DISCLOSURE_TRI_DOWN' if self.conf_session_cache_expanded
            else 'DISCLOSURE_TRI_RIGHT', emboss=False)
        if self.conf_session_cache_expanded:
            box.row().prop(self, "cache_directory", text="Cache directory")

    def generate_supported_types(self):
        self.supported_datablocks.clear()

        for type in bl_types.types_to_register():
            new_db = self.supported_datablocks.add()

            type_module = getattr(bl_types, type)
            type_impl_name = "Bl{}".format(type.split('_')[1].capitalize())
            type_module_class = getattr(type_module, type_impl_name)

            new_db.name = type_impl_name            
            new_db.type_name = type_impl_name
            new_db.bl_delay_refresh = type_module_class.bl_delay_refresh
            new_db.bl_delay_apply =type_module_class.bl_delay_apply
            new_db.use_as_filter = True
            new_db.icon = type_module_class.bl_icon
            new_db.auto_push =type_module_class.bl_automatic_push
            new_db.bl_name=type_module_class.bl_id

classes = (
    ReplicatedDatablock,
    SessionPrefs,
)
def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    prefs = bpy.context.preferences.addons[__package__].preferences
    if len(prefs.supported_datablocks) == 0:
        logger.info('Generating bl_types preferences')
        prefs.generate_supported_types()

def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)