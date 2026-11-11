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

from .installation_validator import ServiceValidator
import os
import bpy


class Draw:

    def __init__(self, extreme_addons_path):
        """Initialize the Draw class with the path to the service configuration and the extreme addons' path.
        :param extreme_addons_path: The path to the extreme addons directory."""

        self.config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
        self.installed_r_list = ServiceValidator(self.config_path).get_resource_lists()
        self.extreme_addons_path = extreme_addons_path

    def draw_requirement_files(self, layout, context=None, use_box=False):
        """Disegna le risorse richieste. Se viene passato context, permette di nascondere/mostrare i dettagli."""

        if context is not None:
            wm = context.window_manager
            if not hasattr(bpy.types.WindowManager, "exa_show_details"):
                bpy.types.WindowManager.exa_show_details = bpy.props.BoolProperty(
                    name="Show Installed Packages",
                    default=False
                )

            box = layout.box()
            row = box.row(align=True)
            icon = 'DISCLOSURE_TRI_DOWN' if wm.exa_show_details else 'DISCLOSURE_TRI_RIGHT'
            row.prop(wm, "exa_show_details", text="Installed Packages & Dependencies", icon=icon, toggle=True,
                     icon_only=False)

            if not wm.exa_show_details:
                return

            target_layout = box.column(align=True)
        else:
            target_layout = layout.box().column(align=True) if use_box else layout.column(align=True)

        target_layout.separator()

        if self.installed_r_list.get("runtimes"):
            target_layout.label(text="Runtimes:", icon='FILE_SCRIPT')
            for runtime in self.installed_r_list["runtimes"]:
                target_layout.label(text=f"  • {runtime}")
            target_layout.separator()

        if self.installed_r_list.get("dependencies"):
            target_layout.label(text="Dependencies:", icon='PACKAGE')
            for dep in self.installed_r_list["dependencies"]:
                target_layout.label(text=f"  • {dep}")
            target_layout.separator()

        if self.installed_r_list.get("assets"):
            target_layout.label(text="Assets & AI Models:", icon='FILE_BACKUP')
            for asset in self.installed_r_list["assets"]:
                target_layout.label(text=f"  • {asset}")

    def draw_installed_requirements(self, layout, config):
        pass

    def draw_exa_ai_core(self, context, layout):
        """Draws the AI Core interface with inline progress bar and collapsible details."""
        col = layout.column(align=True)
        col.label(text="Exa AI Core Engine", icon='CPU')
        col.separator()

        wm = context.window_manager
        is_installing = getattr(wm, "exa_install_running", False)

        if is_installing:
            box_progress = col.box()
            box_progress.label(text="Installing Exa AI Core...", icon='PACKAGE')

            msg = getattr(wm, "exa_install_msg", "")
            if msg:
                box_progress.label(text=msg, icon='INFO')

            if hasattr(wm, "exa_install_progress"):
                box_progress.prop(wm, "exa_install_progress", text="Progress", slider=True)
            col.separator()

        service_ok = ServiceValidator(base_path=self.extreme_addons_path).is_installed()
        if not service_ok:
            box = col.box()
            box.alert = True
            box.label(text="The Exa AI Core is not installed. Install it to enable advanced tools and AI features.",
                      icon='ERROR')
            self.draw_requirement_files(box, context=context)

        else:
            box = col.box()
            box.label(text="The Exa AI Core is installed and active.", icon='CHECKMARK')
            self.draw_requirement_files(box, context=context)

        col.separator()
        row = col.row(align=True)
        row.scale_y = 2
        row.enabled = not is_installing

        if service_ok:
            text = "Reinstall Exa AI Core"
        else:
            text = "Install Exa AI Core"

        ops = row.operator("exa.install_microservice", text=text, icon='DOWNLOAD')
        ops.install_path = self.extreme_addons_path
        ops.options = 'INSTALL'

        if service_ok:
            ops = row.operator("exa.install_microservice", text="Uninstall Exa AI Core", icon='TRASH')
            ops.install_path = self.extreme_addons_path
            ops.options = 'UNINSTALL'
