# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "rcf",
    "author" : "CUBE",
    "description" : "",
    "blender" : (2, 80, 0),
    "location" : "",
    "warning" : "",
    "category" : "Collaboration"
}

from .libs.bsyncio import bsyncio
from . import net_operators
from . import net_ui
import bpy

def register():
    bpy.types.Scene.message = bpy.props.StringProperty(default="Hi")
    bsyncio.register()
    net_operators.register()
    net_ui.register()

def unregister():
    del bpy.types.Scene.message
    bsyncio.unregister()
    net_operators.unregister()
    net_ui.unregister()