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


import threading
import queue

from .config_reader import ConfigReader
from .downloader import ResourceDownloader
from .extractor import ResourceExtractor
from .package_manager import PackageManager


class Orchestrator:
    """
    Coordinates the background pipeline and manages bidirectional communication with Blender.
    """

    def __init__(self, base_path):
        self.base_path = base_path
        self.message_queue = queue.Queue()
        self._cancel_event = threading.Event()
        self.thread = None

    def start_installation_async(self):
        self.thread = threading.Thread(target=self._run_pipeline)
        self.thread.daemon = True
        self.thread.start()

    def request_cancel(self):
        """
        Allows Blender to request cancellation of the operation.
        """
        self._cancel_event.set()
        self.message_queue.put(("CANCELLED", "Cancellation requested by user.", 0.0))

    def _run_pipeline(self):
        try:
            self.message_queue.put(("RUNNING", "Reading configuration...", 0.05))

            if self._cancel_event.is_set():
                return

            reader = ConfigReader(self.base_path)
            plan = reader.get_installation_plan()

            jobs = plan.get("jobs", [])
            if not jobs:
                self.message_queue.put(("FINISHED", "No work to execute.", 1.0))
                return

            if self._cancel_event.is_set():
                return

            self.message_queue.put(("RUNNING", "Downloading resources...", 0.2))
            downloader = ResourceDownloader(plan, self._cancel_event)
            downloader.execute_downloads()

            if self._cancel_event.is_set():
                return

            self.message_queue.put(("RUNNING", "Extracting archives...", 0.6))
            extractor = ResourceExtractor(plan, self._cancel_event)
            extractor.execute_extractions()

            if self._cancel_event.is_set():
                return

            self.message_queue.put(("RUNNING", "Installing dependencies...", 0.8))
            manager = PackageManager(plan, self._cancel_event)
            manager.execute_installations()

            if self._cancel_event.is_set():
                return

            self.message_queue.put(("FINISHED", "Installation completed successfully!", 1.0))

        except Exception as error:
            self.message_queue.put(("ERROR", str(error), 0.0))