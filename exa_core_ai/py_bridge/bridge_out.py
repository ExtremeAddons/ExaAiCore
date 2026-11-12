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

import pickle
import struct
from .core_process import CoreProcess


class Bridge:
    def __init__(self, python_executable, bridge_in_path, payload_dir):
        self.payload_dir = payload_dir
        self._core = CoreProcess(python_executable, bridge_in_path)

    def run(self, module, function, args=None, kwargs=None):
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}

        process = self._core.start()

        request_data = {
            "sys_path": self.payload_dir,
            "module": module,
            "function": function,
            "args": args,
            "kwargs": kwargs
        }

        serialized_request = pickle.dumps(request_data)

        # Inviamo la lunghezza del pacchetto seguita dai dati serializzati
        header = struct.pack('>I', len(serialized_request))
        process.stdin.write(header + serialized_request)
        process.stdin.flush()

        # Leggiamo la risposta del microservizio utilizzando il prefisso di lunghezza
        raw_len = process.stdout.read(4)
        if not raw_len:
            raise RuntimeError("Il microservizio ha chiuso la connessione inaspettatamente.")

        response_length = struct.unpack('>I', raw_len)[0]
        response_bytes = process.stdout.read(response_length)

        response = pickle.loads(response_bytes)

        if not response.get("success"):
            raise RuntimeError(f"Errore nel microservizio:\n{response.get('error')}\n{response.get('trace')}")

        return response.get("result")

    def close(self):
        self._core.close()