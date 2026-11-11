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
import os, json


class Draw:

    def __init__(self, extreme_addons_path):
        """Initialize the Draw class with the path to the service configuration and the extreme addons' path.
        :param extreme_addons_path: The path to the extreme addons directory."""

        self.config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
        self.installed_r_list = ServiceValidator(self.config_path).get_resource_lists()
        self.extreme_addons_path = extreme_addons_path

    def draw_requirement_files(self, layout, use_box=False):

        if use_box:
            b_col = layout.box().column(align=True)
        else:
            b_col = layout.column(align=True)

        b_col.label(text="Required Resources:", icon='INFO')
        b_col.separator()

        if self.installed_r_list.get("runtimes"):
            b_col.label(text="Runtimes:")
            for runtime in self.installed_r_list["runtimes"]:
                b_col.label(text=f"  • {runtime}", icon='FILE_SCRIPT')
            b_col.separator()

        if self.installed_r_list.get("dependencies"):
            b_col.label(text="Dependencies:")
            for dep in self.installed_r_list["dependencies"]:
                b_col.label(text=f"  • {dep}", icon='PACKAGE')
            b_col.separator()

        if self.installed_r_list.get("assets"):
            b_col.label(text="Assets:")
            for asset in self.installed_r_list["assets"]:
                b_col.label(text=f"  • {asset}", icon='FILE_BACKUP')

    def draw_installed_requirements(self, layout, config):
        pass

    def draw_exa_ai_core(self, context, layout):
        """This method """
        col = layout.column(align=True)
        col.label(text="AI Core", icon='INFO')
        col.separator()

        service_ok = ServiceValidator(base_path=self.extreme_addons_path).is_installed()
        if not service_ok:
            # Red alert box with a message to install the AI Core
            box = col.box()
            box.alert = True
            box.label(text="The AI Core is not installed, please install it to use the AI features")
            self.draw_requirement_files(box)

        else:
            # Green box with a message that the AI Core is installed
            box = col.box()
            box.label(text="The AI Core is installed and ready to use", icon='CHECKMARK')
            self.draw_requirement_files(box)

        col.separator()
        row = col.row(align=True)
        row.scale_y = 2
        if service_ok:
            text = "Reinstall Exa Ai Core"
        else:
            text = "Install Exa Ai Core"

        ops = row.operator("exa.install_microservice", text=text, icon='DOWNLOAD')
        ops.install_path = self.extreme_addons_path
        ops.options = 'INSTALL'

        if service_ok:
            row = col.row(align=True)
            row.scale_y = 2
            ops = row.operator("exa.install_microservice", text="Uninstall Exa Ai Core", icon='TRASH')
            ops.install_path = self.extreme_addons_path
            ops.options = 'UNINSTALL'
