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
import shutil
import tarfile
import zipfile


class ResourceExtractor:
    """
    Scansiona i percorsi di destinazione e decompone automaticamente qualsiasi archivio valido trovato,
    normalizzando la struttura nel caso in cui l archivio contenga una cartella radice isolata.
    """

    def __init__(self, plan):
        self.plan = plan

    def execute_extractions(self):
        jobs = self.plan.get("jobs", [])

        for job in jobs:
            target_path = job.get("target_path")
            name = job.get("name")

            if os.path.isfile(target_path):
                self._process_file(target_path, os.path.dirname(target_path), name)

            elif os.path.exists(target_path):
                for filename in os.listdir(target_path):
                    file_path = os.path.join(target_path, filename)
                    if os.path.isfile(file_path):
                        self._process_file(file_path, target_path, name)

    def _process_file(self, file_path, extract_dir, name):
        try:
            contents_before = set(os.listdir(extract_dir))

            if tarfile.is_tarfile(file_path):
                with tarfile.open(file_path, "r:*") as archive:
                    archive.extractall(extract_dir)
                os.remove(file_path)
            elif zipfile.is_zipfile(file_path):
                with zipfile.ZipFile(file_path, "r") as archive:
                    archive.extractall(extract_dir)
                os.remove(file_path)
            else:
                return

            contents_after = set(os.listdir(extract_dir))
            new_items = list(contents_after - contents_before)

            # Se l estrazione ha prodotto una sola cartella e nessun file sparso alla radice,
            # normalizziamo spostando il contenuto fuori da quella cartella wrapper.
            if len(new_items) == 1:
                wrapper_name = new_items[0]
                wrapper_path = os.path.join(extract_dir, wrapper_name)

                if os.path.isdir(wrapper_path):
                    for sub_item in os.listdir(wrapper_path):
                        src_item = os.path.join(wrapper_path, sub_item)
                        dst_item = os.path.join(extract_dir, sub_item)
                        if os.path.exists(dst_item):
                            if os.path.isdir(dst_item):
                                shutil.rmtree(dst_item)
                            else:
                                os.remove(dst_item)
                        shutil.move(src_item, dst_item)
                    os.rmdir(wrapper_path)

        except Exception as error:
            raise RuntimeError(f"Errore durante l estrazione della risorsa {name}: {error}")