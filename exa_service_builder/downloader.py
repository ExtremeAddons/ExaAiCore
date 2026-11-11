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

import hashlib
import os
import urllib.error
import urllib.request


class ResourceDownloader:

    def __init__(self, plan, cancel_event=None, message_queue=None, base_progress=0.05, max_progress=0.70):
        self.plan = plan
        self.cancel_event = cancel_event
        self.message_queue = message_queue
        self.base_progress = base_progress
        self.progress_range = max_progress - base_progress

    def _check_cancel(self):
        if self.cancel_event and self.cancel_event.is_set():
            raise RuntimeError("Operation cancelled.")

    def execute_downloads(self):
        global_dir = self.plan.get("global_target_dir")
        if global_dir and not os.path.exists(global_dir):
            os.makedirs(global_dir, exist_ok=True)

        jobs = [j for j in self.plan.get("jobs", []) if j.get("download_url")]
        total_jobs = len(jobs)

        if total_jobs == 0:
            return

        job_weight = self.progress_range / total_jobs

        for index, job in enumerate(jobs):
            self._check_cancel()

            url = job.get("download_url")
            expected_sha = job.get("sha256")
            target_path = job.get("target_path")
            job_type = job.get("type")
            name = job.get("name")

            if job_type == "asset":
                file_destination = target_path
                parent_dir = os.path.dirname(target_path)
            else:
                parent_dir = target_path
                file_destination = os.path.join(parent_dir, f"{name}.archive")

            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            current_job_base = self.base_progress + (index * job_weight)

            try:
                hasher = hashlib.sha256()

                file_size = 0
                try:
                    req = urllib.request.Request(url, method="HEAD")
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        file_size = int(resp.headers.get("Content-Length", 0))
                except Exception:
                    file_size = 0

                downloaded_bytes = 0

                with urllib.request.urlopen(url, timeout=30) as response, open(file_destination, "wb") as out_file:
                    while True:
                        self._check_cancel()
                        chunk = response.read(1048576)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        hasher.update(chunk)

                        downloaded_bytes += len(chunk)

                        if self.message_queue:
                            if file_size > 0:
                                chunk_progress = (downloaded_bytes / file_size) * job_weight
                            else:
                                chunk_progress = job_weight * 0.5

                            total_p = current_job_base + chunk_progress
                            self.message_queue.put(("RUNNING", f"Downloading {name}", total_p))

                calculated_sha = hasher.hexdigest()
                if expected_sha and calculated_sha != expected_sha:
                    raise ValueError(f"Controllo integrita fallito per la risorsa {name}")

                if self.message_queue:
                    self.message_queue.put(("RUNNING", f"Downloaded {name}", current_job_base + job_weight))

            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as error:
                self._check_cancel()
                raise RuntimeError(f"Errore di rete durante il download di {name}: {error}")
            except (IOError, OSError) as error:
                self._check_cancel()
                raise RuntimeError(f"Errore di scrittura su disco per {name}: {error}")