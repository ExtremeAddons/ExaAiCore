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
import platform
import urllib.request
import urllib.error

class ConfigReader:
    """
    Legge la configurazione e genera un piano di installazione universale ed estendibile.
    """
    def __init__(self, base_path):
        self.base_path = base_path
        self.config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
        self.local_config = self._read_local_config()
        self.manifest = self._fetch_remote_manifest(self.local_config.get("manifest_url"))

        self.os_name = platform.system()
        self.arch_name = platform.machine()
        self.global_target_dir = os.path.join(
            self.base_path,
            self.local_config.get("target_folder_name", "ExaAiCore")
        )

    def _read_local_config(self):
        with open(self.config_path, "r", encoding="utf_8") as file:
            return json.load(file)

    def _fetch_remote_manifest(self, url):
        if not url:
            raise ValueError("Manca il manifest_url nella configurazione")
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode("utf_8"))
        except urllib.error.URLError as error:
            raise RuntimeError(f"Errore nel download del manifest: {error}")

    def _resolve_resource(self, manifest_node, version):
        if not manifest_node:
            return {}
        target_node = manifest_node.get(version, {}) if version else manifest_node
        try:
            return target_node[self.os_name][self.arch_name]
        except KeyError:
            pass
        try:
            return target_node["Universal"]["Universal"]
        except KeyError:
            return {}

    def get_installation_plan(self):
        """
        Restituisce il piano universale completo per il download e la gestione dei pacchetti.
        """
        plan = {
            "global_target_dir": self.global_target_dir,
            "jobs": []
        }

        # Elaborazione Runtimes (Python, PHP, Node, ecc. con i loro package manager)
        local_runtimes = self.local_config.get("runtimes", [])
        manifest_runtimes = self.manifest.get("runtimes", {})

        for runtime in local_runtimes:
            name = runtime.get("name")
            version = runtime.get("version")
            subfolder = runtime.get("target_subfolder", name)

            engine_node = manifest_runtimes.get(name)
            resource_info = self._resolve_resource(engine_node, version)

            plan["jobs"].append({
                "type": "runtime",
                "name": name,
                "version": version,
                "download_url": resource_info.get("url"),
                "sha256": resource_info.get("sha256"),
                "target_path": os.path.join(self.global_target_dir, subfolder),
                "package_manager": runtime.get("dependencies", [])
            })

        # Elaborazione Asset Statici (modelli ONNX, file di supporto)
        local_assets = self.local_config.get("assets", [])
        manifest_assets = self.manifest.get("assets", {})

        for asset in local_assets:
            name = asset.get("name")
            version = asset.get("version")
            subfolder = asset.get("target_subfolder", name)

            asset_node = manifest_assets.get(name)
            resource_info = self._resolve_resource(asset_node, version)

            plan["jobs"].append({
                "type": "asset",
                "name": name,
                "version": version,
                "download_url": resource_info.get("url"),
                "sha256": resource_info.get("sha256"),
                "target_path": os.path.join(self.global_target_dir, subfolder)
            })

        return plan