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

import subprocess
import threading


class CoreProcess:

    def __init__(self):
        self.process = None
        self.lock = threading.Lock()

    def start(self):

        with self.lock:

            if self.process is not None:
                if self.process.poll() is None:
                    return self.process

            self.process = subprocess.Popen(
                [
                    python_executable,
                    bridge_in_path
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )

            return self.process

    def close(self):

        with self.lock:

            if self.process is not None:

                if self.process.poll() is None:
                    self.process.terminate()
                    self.process.wait()

                self.process = None