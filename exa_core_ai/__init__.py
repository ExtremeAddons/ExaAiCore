#   #
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version
#    of the License, or (at your option) any later version.
#   #
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#   #
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software Foundation,
#    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#   #
#   Copyright 2019-2026(C) Andrea Donati

import bpy

from .icons import register_custom_icons, unregister_custom_icons
from .installer.bl_draw import EXAAICORE_OT_toggle_details
from .installer.bl_ops_installer import EXAAICORE_OT_installer


installer_classes = [
    EXAAICORE_OT_installer,
    EXAAICORE_OT_toggle_details
]


def register_ai_exa_core():
    for cls in installer_classes:
        bpy.utils.register_class(cls)

    register_custom_icons()


def unregister_ai_exa_core():
    for cls in installer_classes:
        bpy.utils.unregister_class(cls)

    unregister_custom_icons()