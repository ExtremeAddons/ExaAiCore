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
import hashlib
import urllib.request
import urllib.error

class ResourceDownloader:
    def __init__(self, plan):
        self.plan = plan

    def execute_downloads(self):
        global_dir = self.plan.get("global_target_dir")
        if global_dir and not os.path.exists(global_dir):
            os.makedirs(global_dir, exist_ok=True)

        jobs = self.plan.get("jobs", [])
        for job in jobs:
            url = job.get("download_url")
            expected_sha = job.get("sha256")
            target_path = job.get("target_path")
            job_type = job.get("type")
            name = job.get("name")

            if not url:
                continue

            if job_type == "asset":
                file_destination = target_path
                parent_dir = os.path.dirname(target_path)
            else:
                parent_dir = target_path
                file_destination = os.path.join(parent_dir, f"{name}.archive")

            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            try:
                hasher = hashlib.sha256()
                with urllib.request.urlopen(url, timeout=30) as response, open(file_destination, "wb") as out_file:
                    while True:
                        chunk = response.read(1048576)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        hasher.update(chunk)

                calculated_sha = hasher.hexdigest()
                if calculated_sha != expected_sha:
                    raise ValueError(f"Controllo integrità fallito per la risorsa {name}")

            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as error:
                raise RuntimeError(f"Errore di rete durante il download di {name}: {error}")
            except (IOError, OSError) as error:
                raise RuntimeError(f"Errore di scrittura su disco per {name}: {error}")