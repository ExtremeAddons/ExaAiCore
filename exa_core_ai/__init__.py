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
import os

import bpy

from .py_bridge import set_payload_dir
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

    addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tasks_dir = os.path.join(addon_root, "exa_tasks")
    set_payload_dir(tasks_dir)


def unregister_ai_exa_core():

    from .py_bridge import bridge
    if bridge is not None:
        bridge.close() # Chiude l'eventuale python isolato come demone se è stato avviato

    for cls in installer_classes:
        bpy.utils.unregister_class(cls)

    unregister_custom_icons()