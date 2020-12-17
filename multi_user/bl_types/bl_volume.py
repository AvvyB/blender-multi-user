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


import bpy
import mathutils
from pathlib import Path

from .dump_anything import Loader, Dumper
from .bl_datablock import BlDatablock, get_datablock_from_uuid


class BlVolume(BlDatablock):
    bl_id = "volumes"
    bl_class = bpy.types.Volume
    bl_delay_refresh = 1
    bl_delay_apply = 1
    bl_automatic_push = True
    bl_check_common = False
    bl_icon = 'VOLUME_DATA'
    bl_reload_parent = False

    def _load_implementation(self, data, target):
        loader = Loader()
        loader.load(target, data)
        loader.load(target.display, data['display'])

        # MATERIAL SLOTS
        target.materials.clear()

        for mat_uuid, mat_name in data["material_list"]:
            mat_ref = None
            if mat_uuid is not None:
                mat_ref = get_datablock_from_uuid(mat_uuid, None)
            else:
                mat_ref = bpy.data.materials.get(mat_name, None)

            if mat_ref is None:
                raise Exception("Material doesn't exist")

            target.materials.append(mat_ref)

    def _construct(self, data):
        return bpy.data.volumes.new(data["name"])

    def _dump_implementation(self, data, instance=None):
        assert(instance)

        dumper = Dumper()
        dumper.depth = 1
        dumper.exclude_filter = [
            'tag',
            'original',
            'users',
            'uuid',
            'is_embedded_data',
            'is_evaluated',
            'name_full',
            'use_fake_user'
        ]

        data = dumper.dump(instance)

        data['display'] = dumper.dump(instance.display)

         # Fix material index
        data['material_list'] = [(m.uuid, m.name) for m in instance.materials if m]

        return data

    def _resolve_deps_implementation(self):
        # TODO: resolve material
        deps = []

        external_vdb = Path(bpy.path.abspath(self.instance.filepath))
        if external_vdb.exists() and not external_vdb.is_dir():
            deps.append(external_vdb)

        for material in self.instance.materials:
            if material:
                deps.append(material)

        return deps


