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
        self, server_host="localhost", server_port=8000, max_retries=5, retry_delay=1
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client_socket = None
        self.connected = False
        self.connect()

    def connect(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.server_host, self.server_port))
                print(f"Connected to {self.server_host}:{self.server_port}")
                self.connected = True
                if len(sys.argv) > 1:
                    self.client_name = sys.argv[1]
                else:
                    self.client_name = f"user-{generate_random_string()}"

                self.client_socket.sendall(encode_message(self.client_name))
                time.sleep(0.1)
                self.receive_thread = threading.Thread(target=self.receive_messages)
                time.sleep(0.1)
                self.send_thread = threading.Thread(target=self.send_messages)
                break
            except Exception as e:
                retries += 1
                print(f"Connection failed (Attempt {retries}/{self.max_retries}): {e}")
                if retries < self.max_retries:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print("Maximum retries reached. Exiting...")
                    return

    def start(self):
        self.receive_thread.start()
        self.send_thread.start()
        self.receive_thread.join()
        self.send_thread.join()
        self.client_socket.close()

    def receive_messages(self):
        while True:
            if not self.connected:
                self.connect()
                if not self.connected:
                    break
            try:
                message = receive_message(self.client_socket)
                if message is False:
                    print("Connection closed by the server")
                    self.connected = False
                    self.client_socket.close()
                    time.sleep(self.retry_delay)
                    continue

                print(sender_colored_message(*deserialize_message(message)))

            except ConnectionResetError:
                print("Connection reset by peer. Reconnecting...")
                self.connected = False
                self.client_socket.close()
                time.sleep(self.retry_delay)

            except Exception as e:
                print(f"Error receiving message: {e}")
                self.connected = False
                self.client_socket.close()
                time.sleep(self.retry_delay)

    def send_messages(self):
        while True:
            message = input()
            if message:
                self.client_socket.sendall(encode_message(message))


if __name__ == "__main__":
    client = Client()
    client.start()
