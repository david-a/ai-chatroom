import socket
import threading
import sys

from lib.utils import (
    deserialize_message,
    sender_colored_message,
    encode_message,
    generate_random_string,
    receive_message,
)


class Client:
    def __init__(self, server_host="localhost", server_port=8000):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_host, self.server_port))
        print(f"Connected to {self.server_host}:{self.server_port}")

        if len(sys.argv) > 1:
            self.client_name = sys.argv[1]
        else:
            self.client_name = f"Client-{generate_random_string()}"

        self.client_socket.sendall(encode_message(self.client_name))

        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.send_thread = threading.Thread(target=self.send_messages)

    def start(self):
        self.receive_thread.start()
        self.send_thread.start()
        self.receive_thread.join()
        self.send_thread.join()
        self.client_socket.close()

    def receive_messages(self):
        while True:
            try:
                message = receive_message(self.client_socket)
                if message is False:
                    print("Connection closed by the server")
                    break

                print(sender_colored_message(*deserialize_message(message)))

            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def send_messages(self):
        while True:
            message = input()
            if message:
                self.client_socket.sendall(encode_message(message))


if __name__ == "__main__":
    client = Client()
    client.start()
