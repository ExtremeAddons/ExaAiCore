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
import threading
from concurrent.futures import ThreadPoolExecutor
from .core_process import CoreProcess


class Bridge:
    """Client-side bridge that communicates with an isolated Python worker process.

    The Bridge serializes requests using pickle and exchanges them over the
    subprocess stdin/stdout pipes, framing each payload with a 4-byte big-endian
    length header. It supports both synchronous and asynchronous execution modes.
    """

    def __init__(self, python_executable, bridge_in_path, payload_dir):
        """Initialize the Bridge with the worker process configuration.

        Args:
            python_executable (str): Path to the isolated Python interpreter executable.
            bridge_in_path (str): Path to the worker entry-point script (bridge_in).
            payload_dir (str): Directory containing the AI modules to be loaded by the worker.
        """
        self.payload_dir = payload_dir
        self._core = CoreProcess(python_executable, bridge_in_path)
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1)

    def _send_request(self, request_data):
        """Serialize and send a request to the worker, then read the response.

        The communication protocol is:
            1. Write a 4-byte big-endian length header followed by pickled payload.
            2. Read a 4-byte length header from stdout.
            3. Read the pickled response and deserialize it.

        Args:
            request_data (dict): The request dictionary to send to the worker.

        Returns:
            The deserialized result from the worker.

        Raises:
            RuntimeError: If the connection is closed unexpectedly or the worker reports an error.
        """
        with self._lock:
            process = self._core.start()
            serialized_request = pickle.dumps(request_data)

            # Frame the payload with a 4-byte big-endian length header
            header = struct.pack('>I', len(serialized_request))
            process.stdin.write(header + serialized_request)
            process.stdin.flush()

            # Read the response length header
            raw_len = process.stdout.read(4)
            if not raw_len:
                raise RuntimeError("Connection closed unexpectedly.")

            response_length = struct.unpack('>I', raw_len)[0]
            response_bytes = process.stdout.read(response_length)
            response = pickle.loads(response_bytes)

            # Raise an error if the worker reported a failure
            if not response.get("success"):
                error_msg = response.get('error')
                trace_msg = response.get('trace')
                raise RuntimeError(f"Process error:\n{error_msg}\n{trace_msg}")

            return response.get("result")

    def execute(self, request_data, sync=True):
        """Execute a request against the worker process.

        Args:
            request_data (dict): The request payload to send.
            sync (bool): If True, block until the result is available.
                        If False, return a concurrent.futures.Future object.

        Returns:
            The worker result, or a Future if sync is False.
        """
        if sync:
            return self._send_request(request_data)
        else:
            return self._executor.submit(self._send_request, request_data)

    def run(self, module, function, args=None, kwargs=None, sync=True):
        """Invoke a standalone function inside the isolated worker.

        Args:
            module (str): Dotted path to the module containing the target function.
            function (str): Name of the function to call.
            args (tuple, optional): Positional arguments to pass to the function.
            kwargs (dict, optional): Keyword arguments to pass to the function.
            sync (bool): If True, block until completion; otherwise return a Future.

        Returns:
            The function's return value, or a Future if sync is False.
        """
        req = {
            "action": "run_function",
            "sys_path": self.payload_dir,
            "module": module,
            "function": function,
            "args": args or (),
            "kwargs": kwargs or {}
        }
        return self.execute(req, sync)

    def instantiate(self, module, class_name, args=None, kwargs=None, sync=True):
        """Instantiate a class inside the isolated worker and register the instance.

        Args:
            module (str): Dotted path to the module containing the target class.
            class_name (str): Name of the class to instantiate.
            args (tuple, optional): Positional arguments for the constructor.
            kwargs (dict, optional): Keyword arguments for the constructor.
            sync (bool): If True, block until completion; otherwise return a Future.

        Returns:
            A dict containing the instance_id and any constructor return data, or a Future.
        """
        req = {
            "action": "instantiate",
            "sys_path": self.payload_dir,
            "module": module,
            "class_name": class_name,
            "args": args or (),
            "kwargs": kwargs or {}
        }
        return self.execute(req, sync)

    def call_method(self, instance_id, method, args=None, kwargs=None, sync=True):
        """Call a method on a previously instantiated object in the worker.

        Args:
            instance_id (str): Identifier of the registered instance to target.
            method (str): Name of the method to invoke.
            args (tuple, optional): Positional arguments for the method call.
            kwargs (dict, optional): Keyword arguments for the method call.
            sync (bool): If True, block until completion; otherwise return a Future.

        Returns:
            The method's return value, or a Future if sync is False.
        """
        req = {
            "action": "call_method",
            "sys_path": self.payload_dir,
            "instance_id": instance_id,
            "method": method,
            "args": args or (),
            "kwargs": kwargs or {}
        }
        return self.execute(req, sync)

    def free_instance(self, instance_id, sync=True):
        """Release a previously instantiated object in the worker to free memory.

        Args:
            instance_id (str): Identifier of the instance to release.
            sync (bool): If True, block until completion; otherwise return a Future.

        Returns:
            Confirmation response from the worker, or a Future if sync is False.
        """
        req = {
            "action": "free_instance",
            "sys_path": self.payload_dir,
            "instance_id": instance_id
        }
        return self.execute(req, sync)

    def close(self):
        """Shut down the thread pool and terminate the worker process."""
        self._executor.shutdown(wait=False)
        self._core.close()