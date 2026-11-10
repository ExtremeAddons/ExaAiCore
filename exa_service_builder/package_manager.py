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
import subprocess
import threading


class PackageManager:
    """
    Gestisce l installazione delle dipendenze per ciascun runtime presente nel piano,
    monitorando attivamente la cancellazione ed eseguendo i comandi in modo universale.
    """

    def __init__(self, plan, cancel_event=None):
        self.plan = plan
        self.cancel_event = cancel_event

    def _check_cancel(self):
        if self.cancel_event and self.cancel_event.is_set():
            raise RuntimeError("Operation cancelled.")

    def execute_installations(self):
        jobs = self.plan.get("jobs", [])

        for job in jobs:
            self._check_cancel()

            if job.get("type") != "runtime":
                continue

            target_path = job.get("target_path")
            executable = job.get("executable")
            args = job.get("args", [])
            dependencies = job.get("dependencies", [])

            if not executable or not dependencies:
                continue

            executable_path = os.path.join(target_path, executable)
            if not os.path.exists(executable_path):
                raise FileNotFoundError(f"Eseguibile non trovato in {executable_path}")

            cmd = [executable_path] + args + dependencies

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            while process.poll() is None:
                self._check_cancel()
                threading.Event().wait(0.1)

            if process.returncode != 0:
                _, stderr = process.communicate()
                raise RuntimeError(f"Errore durante l installazione delle dipendenze: {stderr}")