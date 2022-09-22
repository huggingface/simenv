import atexit
import base64
import json
import signal
import socket
import subprocess
import time

from .engine import Engine


NUM_BIND_RETRIES = 20
BIND_RETRIES_DELAY = 2.0
SOCKET_TIME_OUT = 30.0  # Timeout in seconds


class UnityEngine(Engine):
    def __init__(
        self,
        scene,
        auto_update=True,
        engine_exe="",
        engine_port=None,
        engine_headless=False,
    ):
        super().__init__(scene=scene, auto_update=auto_update)

        self.host = "127.0.0.1"
        self.port = engine_port if engine_port is not None else 55000

        if engine_exe:
            self._launch_executable(executable=engine_exe, port=engine_port, headless=engine_headless)

        self._initialize_server()
        atexit.register(self._close)
        signal.signal(signal.SIGTERM, self._close)
        signal.signal(signal.SIGINT, self._close)

        self._map_pool = False

    def _launch_executable(self, executable: str, port: str, headless: bool):
        # TODO: improve headless training check on a headless machine
        if headless:
            print("launching env headless")
            launch_command = f"{executable} -batchmode -nographics --args port {port}".split(" ")
        else:
            launch_command = f"{executable} --args port {port}".split(" ")
        self.proc = subprocess.Popen(
            launch_command,
            start_new_session=False,
        )

    def _initialize_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        print(f"Server started. Waiting for connection on {self.host} {self.port}...")
        try:
            self.socket.bind((self.host, self.port))
        except OSError:
            for n in range(NUM_BIND_RETRIES):
                time.sleep(BIND_RETRIES_DELAY)
                try:
                    self.socket.bind((self.host, self.port))
                    break
                except OSError:
                    print(f"port {self.port} is still in use, trying again")
            raise Exception(f"Could not bind to port {self.port}")

        self.socket.listen()
        self.client, self.client_address = self.socket.accept()
        # self.client.setblocking(0)  # Set to non-blocking
        self.client.settimeout(SOCKET_TIME_OUT)  # Set a timeout
        print(f"Connection from {self.client_address}")

    def _get_response(self):
        while True:

            data_length = self.client.recv(4)
            data_length = int.from_bytes(data_length, "little")

            if data_length:
                response = ""  # TODO: string concatenation may be slow
                while len(response) < data_length:
                    response += self.client.recv(data_length - len(response)).decode()

                # print(f"Received response: {response}")
                return response

    def update_asset(self, root_node):
        # TODO update and make this API more consistent with all the
        # update_asset, update, show
        pass

    def update_all_assets(self):
        pass

    def show(self, **kwargs):
        bytes = self._scene.as_glb_bytes()
        b64_bytes = base64.b64encode(bytes).decode("ascii")
        kwargs.update({"b64bytes": b64_bytes})
        return self.run_command("Initialize", **kwargs)

    def step(self, action=None, **kwargs):
        """Step the environment with the given action.

        Args:
            action (dict): The action to take in the environment.
                If the action is None, we don't send an action to the environment.
                We then only send the Step command to Unity to step the physics engine.
        """
        if action is not None:
            kwargs.update({"action": action})
        return self.run_command("Step", **kwargs)

    def step_send_async(self, **kwargs):
        self.run_command_async("Step", **kwargs)

    def step_recv_async(self):
        return self.get_response_async()

    def reset(self):
        return self.run_command("Reset")

    def run_command(self, command, wait_for_response=True, **kwargs):
        message = json.dumps({"type": command, **kwargs})
        message_bytes = len(message).to_bytes(4, "little") + bytes(message.encode())
        self.client.sendall(message_bytes)
        if wait_for_response:
            response = self._get_response()
            try:
                return json.loads(response)
            except Exception:
                return response

    def run_command_async(self, command, **kwargs):
        message = json.dumps({"type": command, **kwargs})
        message_bytes = len(message).to_bytes(4, "little") + bytes(message.encode())
        self.client.sendall(message_bytes)

    def get_response_async(self):
        response = self._get_response()
        try:
            return json.loads(response)
        except Exception:
            return response

    def _close(self):
        # print("exit was not clean, using atexit to close env")
        self.close()

    def close(self):
        try:
            self.run_command("Close", wait_for_response=False)
        except Exception as e:
            print("exception sending close message", e)

        # print("closing client")
        # self.client.shutdown(socket.SHUT_RDWR)
        self.client.close()
        self.socket.close()

        try:
            atexit.unregister(self._close)
        except Exception as e:
            print("exception unregistering close method", e)