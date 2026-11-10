"""
Module for reading configuration files and building the installation plan
"""

import json
import os
import platform
import urllib.request
import urllib.error

class ConfigReader:
    """
    A class to read the local config, fetch the remote manifest,
    and generate a unified installation plan.
    """

    @staticmethod
    def read_local_config(config_path):
        """Legge il file JSON di configurazione locale."""
        with open(config_path, "r", encoding="utf_8") as file:
            return json.load(file)

    @staticmethod
    def fetch_remote_manifest(url):
        """Scarica e converte in dizionario il manifest remoto."""
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode("utf_8"))
        except urllib.error.URLError as error:
            raise RuntimeError(f"Errore nel download del manifest: {error}")

    @staticmethod
    def resolve_url(manifest_node, version, os_name, arch_name):
        """
        Risolve URL cercando la corrispondenza hardware esatta.
        Se presente una versione scende di livello.
        Ripiega su Universal se la risorsa è multipiattaforma.
        """
        if not manifest_node:
            return None

        # Navigazione condizionale basata sulla versione
        target_node = manifest_node.get(version, {}) if version else manifest_node

        # Tentativo per Sistema Operativo e Architettura
        try:
            return target_node[os_name][arch_name]
        except KeyError:
            pass

        # Tentativo per file Universale
        try:
            return target_node["Universal"]["Universal"]
        except KeyError:
            return None

    @staticmethod
    def build_installation_plan(base_path):
        """
        Genera il piano di installazione completo unendo config locale e manifest remoto.
        """
        # Lettura configurazione
        config_path = os.path.join(os.path.dirname(__file__), "service_config.json")
        config = ConfigReader.read_local_config(config_path)

        manifest_url = config.get("manifest_url")
        if not manifest_url:
            raise ValueError("Manca il manifest_url nel file di configurazione")

        manifest = ConfigReader.fetch_remote_manifest(manifest_url)

        # Preparazione ambiente
        target_folder = config.get("target_folder_name", "ExaAiCore")
        global_target_dir = os.path.join(base_path, target_folder)

        os_name = platform.system()
        arch_name = platform.machine()

        # Struttura del piano di esecuzione
        plan = {
            "global_target_dir": global_target_dir,
            "jobs": []
        }

        # Processamento dei Motori
        runtimes = config.get("runtimes", [])
        manifest_engines = manifest.get("engines", {})

        for runtime in runtimes:
            name = runtime.get("name")
            version = runtime.get("version")
            subfolder = runtime.get("target_subfolder", name)

            engine_node = manifest_engines.get(name)
            download_url = ConfigReader.resolve_url(engine_node, version, os_name, arch_name)

            plan["jobs"].append({
                "type": "runtime",
                "name": name,
                "version": version,
                "download_url": download_url,
                "target_path": os.path.join(global_target_dir, subfolder),
                "dependencies": runtime.get("dependencies", [])
            })

        # Processamento degli Asset Statici
        assets = config.get("assets", [])
        manifest_assets = manifest.get("assets", {})

        for asset in assets:
            name = asset.get("name")
            version = asset.get("version")
            subfolder = asset.get("target_subfolder", name)

            asset_node = manifest_assets.get(name)
            download_url = ConfigReader.resolve_url(asset_node, version, os_name, arch_name)

            plan["jobs"].append({
                "type": "asset",
                "name": name,
                "version": version,
                "download_url": download_url,
                "target_path": os.path.join(global_target_dir, subfolder)
            })

        return plan