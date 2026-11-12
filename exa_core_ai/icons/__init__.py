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
#   Copyright 2019 2026(C) Andrea Donati
#

import bpy
import os
from .interfaceicons import ExaCoreAiIcons
path = os.path.join(os.path.dirname(__file__), 'asset')


def register_custom_icons():
    ExaCoreAiIcons.custom_icons = bpy.utils.previews.new()
    for idx, ic in enumerate(os.listdir(path)):
        if not ic.startswith("."):
            if ic.endswith(".png") or ic.endswith(".jpg") or ic.endswith(".jpeg") or ic.endswith(".webp"):
                ExaCoreAiIcons.custom_icons.load(ic, os.path.join(path, ic), 'IMAGE')

def unregister_custom_icons():
    if ExaCoreAiIcons.custom_icons:
        bpy.utils.previews.remove(ExaCoreAiIcons.custom_icons)
        ExaCoreAiIcons.custom_icons.clear()

