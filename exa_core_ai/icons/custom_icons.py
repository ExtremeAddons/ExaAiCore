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

import os
import bpy
import bpy.utils.previews


class CustomIconManager:
    """Gestore indipendente e incapsulato per le icone custom dell'addon."""

    def __init__(self, icons_dir_name="icons"):
        self.icons_dir = os.path.join(os.path.dirname(__file__), icons_dir_name)
        self.custom_icons = None
        self._enum_cache = []

    def register(self):
        """Carica tutte le immagini presenti nella cartella delle icone."""
        if self.custom_icons is not None:
            return

        self.custom_icons = bpy.utils.previews.new()
        self._enum_cache.clear()

        if not os.path.exists(self.icons_dir):
            return

        valid_extensions = (".png", ".jpg", ".jpeg", ".webp")
        for idx, filename in enumerate(sorted(os.listdir(self.icons_dir))):
            if filename.startswith("."):
                continue
            if filename.lower().endswith(valid_extensions):
                name_without_ext = os.path.splitext(filename)[0]
                filepath = os.path.join(self.icons_dir, filename)
                # Carica l'icona usando il nome file intero come chiave
                self.custom_icons.load(filename, filepath, 'IMAGE')

                # Prepara la tupla per gli EnumProperty di Blender (nome, etichetta, descrizione, icon_id, index)
                self._enum_cache.append(
                    (name_without_ext, name_without_ext.title(), "", self.custom_icons[filename].icon_id, idx))

    def unregister(self):
        """Pulisce e rimuove le anteprime dalla memoria di Blender."""
        if self.custom_icons:
            bpy.utils.previews.remove(self.custom_icons)
            self.custom_icons = None
        self._enum_cache.clear()

    def get_icon_id(self, icon_name):
        """Restituisce l'icon_id di Blender dato il nome del file (con o senza estensione)."""
        if not self.custom_icons:
            return 0

        # Cerca sia con l'estensione che senza
        target = icon_name if icon_name.endswith((".png", ".jpg", ".jpeg", ".webp")) else f"{icon_name}.png"

        if target in self.custom_icons:
            return self.custom_icons[target].icon_id
        return 0

    def get_enum_items(self, self_prop, context):
        """Metodo callback utilizzabile direttamente dentro un EnumProperty."""
        return self._enum_cache