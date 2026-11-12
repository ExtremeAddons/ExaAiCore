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

import json
import os


class LocalConfigWriter:
    def __init__(self, plan):
        self.plan = plan

    def write_config(self):
        global_target_dir = os.path.abspath(self.plan.get("global_target_dir"))
        bridge_in_path = os.path.join(global_target_dir, "bridge_in.py")

        config_data = {
            "install_path": global_target_dir,
            "bridge_in_path": bridge_in_path,
            "runtimes": {},
            "assets": {}
        }

        for job in self.plan.get("jobs", []):
            job_type = job.get("type")
            name = job.get("name")
            target_path = job.get("target_path")

            if not name or not target_path:
                continue

            if job_type == "runtime":
                executable = job.get("executable")
                if executable:
                    config_data["runtimes"][name] = os.path.abspath(
                        os.path.join(target_path, executable)
                    )

            elif job_type == "asset":
                config_data["assets"][name] = os.path.abspath(target_path)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.abspath(os.path.join(current_dir, "..", "local_config.json"))

        with open(config_path, "w", encoding="utf8") as f:
            json.dump(config_data, f, indent=4)