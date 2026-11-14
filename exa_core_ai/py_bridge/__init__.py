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

from .bridge_out import Bridge
from .bridge_out import Bridge
from ..local_config_reader import LocalConfigReader

_instances = {}
_default_payload_dir = None


def set_payload_dir(payload_dir):
    """Imposta la cartella dei task dell'addon ospite."""
    global _default_payload_dir
    _default_payload_dir = os.path.abspath(payload_dir)
    for instance in _instances.values():
        instance.payload_dir = _default_payload_dir


def get_bridge(runtime_name="python", payload_dir=None):
    """Restituisce o inizializza il bridge per il runtime richiesto."""
    target_payload = os.path.abspath(payload_dir) if payload_dir else _default_payload_dir

    if runtime_name in _instances:
        instance = _instances[runtime_name]
        if target_payload:
            instance.payload_dir = target_payload
        return instance

    reader = LocalConfigReader()
    if not reader.is_available():
        return None

    try:
        executable = reader.get_runtime(runtime_name)
        bridge_in_path = reader.get_bridge_in_path()
        instance = Bridge(executable, bridge_in_path, target_payload)
        _instances[runtime_name] = instance
        return instance
    except KeyError as error:
        print(f"Errore configurazione Bridge: {error}")
        return None


class _LazyBridge:
    """Proxy leggero che risolve il bridge solo al momento dell'uso effettivo."""

    def __getattr__(self, name):
        instance = get_bridge("python")
        if instance is None:
            raise RuntimeError("Servizio ExaCoreAi non ancora installato.")
        return getattr(instance, name)

    def __bool__(self):
        return get_bridge("python") is not None


bridge = _LazyBridge()
