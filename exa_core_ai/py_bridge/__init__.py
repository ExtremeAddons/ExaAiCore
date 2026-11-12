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

# py_bridge

import os
from ..local_config_reader import LocalConfigReader
from .bridge_out import Bridge


def get_bridge(runtime_name="python"):
    """
    Inizializza il bridge dinamicamente in base al motore richiesto.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    payload_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "remote_payloads"))

    reader = LocalConfigReader()

    # Prevenzione crash: se il servizio non e ancora installato, restituisce None
    if not reader.is_available():
        return None

    try:
        # Recupera in modo universale il percorso dell eseguibile richiesto
        executable = reader.get_runtime(runtime_name)
        bridge_in_path = reader.get_bridge_in_path()

        return Bridge(executable, bridge_in_path, payload_dir)
    except KeyError as error:
        print(f"Errore configurazione Bridge: {error}")
        return None


# Variabile globale per mantenere la compatibilita con le chiamate standard dell addon
bridge = get_bridge("python")
