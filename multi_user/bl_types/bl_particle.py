import bpy
import mathutils

from . import dump_anything
from .bl_datablock import BlDatablock, get_datablock_from_uuid


def dump_textures_slots(texture_slots: bpy.types.bpy_prop_collection) -> list:
    """ Dump every texture slot collection as the form:
        [(index, slot_texture_uuid, slot_texture_name), (), ...]
    """
    dumped_slots = []
    for index, slot in enumerate(texture_slots):
        if slot and slot.texture:
            dumped_slots.append((index, slot.texture.uuid, slot.texture.name))

    return dumped_slots


def load_texture_slots(dumped_slots: list, target_slots: bpy.types.bpy_prop_collection):
    """
    """
    for index, slot in enumerate(target_slots):
        if slot:
            target_slots.clear(index)

    for index, slot_uuid, slot_name in dumped_slots:
        target_slots.create(index).texture = get_datablock_from_uuid(
            slot_uuid, slot_name
        )

IGNORED_ATTR = [
    "is_embedded_data",
    "is_evaluated",
    "is_fluid",
    "is_library_indirect",
    "users"
]

class BlParticle(BlDatablock):
    bl_id = "particles"
    bl_class = bpy.types.ParticleSettings
    bl_icon = "PARTICLES"
    bl_check_common = False
    bl_reload_parent = False

    def _construct(self, data):
        instance = bpy.data.particles.new(data["name"])
        instance.uuid = self.uuid
        return instance

    def _load_implementation(self, data, target):
        dump_anything.load(target, data)

        dump_anything.load(target.effector_weights, data["effector_weights"])

        # Force field
        force_field_1 = data.get("force_field_1", None)
        if force_field_1:
            dump_anything.load(target.force_field_1, force_field_1)

        force_field_2 = data.get("force_field_2", None)
        if force_field_2:
            dump_anything.load(target.force_field_2, force_field_2)

        # Texture slots
        load_texture_slots(data["texture_slots"], target.texture_slots)

    def _dump_implementation(self, data, instance=None):
        assert instance

        dumper = dump_anything.Dumper()
        dumper.depth = 1
        dumper.exclude_filter = IGNORED_ATTR
        data = dumper.dump(instance)

        # Particle effectors
        data["effector_weights"] = dumper.dump(instance.effector_weights)
        if instance.force_field_1:
            data["force_field_1"] = dumper.dump(instance.force_field_1)
        if instance.force_field_2:
            data["force_field_2"] = dumper.dump(instance.force_field_2)

        # Texture slots
        data["texture_slots"] = dump_textures_slots(instance.texture_slots)

        return data

    def _resolve_deps_implementation(self):
        return [t.texture for t in self.instance.texture_slots if t and t.texture]
