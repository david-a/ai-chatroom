import socket
import threading
import sys
import time

from lib.utils import (
    deserialize_message,
    sender_colored_message,
    encode_message,
    generate_random_string,
    receive_message,
)


class Client:
    def __init__(
        self,
        server_host="localhost",
        server_port=8000,
        max_retries=5,
        retry_delay=1,
        name=None,
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client_socket = None
        self.connected = False
        self.finished = False
        if len(sys.argv) > 1:
            self.client_name = sys.argv[1]
        else:
            self.client_name = name or f"user-{generate_random_string()}"

    def connect(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.connected = True
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.server_host, self.server_port))
                print(f"[CLIENT] Connected to {self.server_host}:{self.server_port}")
                break
            except Exception as e:
                retries += 1
                print(
                    f"[CLIENT] Connection failed (Attempt {retries}/{self.max_retries}): {e}"
                )
                if retries < self.max_retries:
                    print(f"[CLIENT] Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print("[CLIENT] Maximum retries reached. Exiting...")
                    return

    def register(self):
        self.client_socket.sendall(encode_message(self.client_name))
        time.sleep(0.1)
        self.receive_thread = threading.Thread(target=self.receive_messages)
        time.sleep(0.1)
        self.send_thread = threading.Thread(target=self.send_messages)
        self.receive_thread.start()
        self.send_thread.start()

    def connect_and_register(self):
        if not self.connected:
            self.connect()
            if self.connected:
                self.register()
                return True
            else:
                return False
        return True

    def start(self):
        self.connect_and_register()
        self.receive_thread.join()
        self.send_thread.join()
        self.close_connection()

    def stop(self):
        self.finished = True

    def receive_message(self):
        message = receive_message(self.client_socket)
        if message is False:
            print("[CLIENT] Connection closed by the server")
            self.reset_connection()
        else:
            print(sender_colored_message(*deserialize_message(message)))

    def send_message(self):
        message = input()
        if message:
            self.client_socket.sendall(encode_message(message))

    def send_messages(self):
        self.retriable_loop(self.send_message, "send_messages")

    def receive_messages(self):
        self.retriable_loop(self.receive_message, "receive_messages")

    def close_connection(self):
        self.client_socket.close()
        self.connected = False

    def reset_connection(self):
        self.close_connection()
        time.sleep(self.retry_delay)

    def retriable_loop(self, func, func_name):
        while not self.finished:
            if not self.connect_and_register():
                break
            try:
                func()
            except ConnectionResetError:
                print(
                    f"[CLIENT] {func_name} - Connection reset by peer. Reconnecting..."
                )
                self.reset_connection()
            except ConnectionAbortedError:
                print(f"[CLIENT] {func_name} - Connection aborted. Reconnecting...")
                self.reset_connection()
            except ConnectionRefusedError:
                print(f"[CLIENT] {func_name} - Connection refused. Reconnecting...")
                self.reset_connection()
            except KeyboardInterrupt:
                print(f"[CLIENT] {func_name} - Exiting...")
                self.close_connection()
                break
            except Exception as e:
                print(f"[CLIENT] Error in {func_name}: {e}")
                self.reset_connection()
        self.close_connection()


if __name__ == "__main__":
    client = Client()
    client.start()
