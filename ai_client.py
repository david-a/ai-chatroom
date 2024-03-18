import socket
import threading
import time

from client import Client
from lib.ai_utils import ai_call
from lib.utils import (
    deserialize_message,
    encode_message,
    generate_random_string,
    receive_message,
    sender_colored_message,
    serialize_message,
)

SYSTEM_PROMPT_RESPOND = (
    "You are a joyful chat participant. respond in the context of the conversation."
)
SYSTEM_PROMPT_DISRUPT = (
    "You are a joyful chat participant. Initiate a conversation with a random sentence."
)


class AIClient(Client):
    def __init__(
        self,
        server_host="localhost",
        server_port=8000,
        max_retries=5,
        retry_delay=1,
        mode=None,
        n=None,
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connected = False

        self.conversation_log = []
        self.mode = mode or self.get_mode()
        self.n = n or self.get_n()

        self.client_name = f"AI-{generate_random_string()}"

        self.connect_and_register()

    def register(self):
        self.client_socket.sendall(encode_message(self.client_name))

        self.receive_thread = threading.Thread(target=self.receive_messages)
        if self.mode == 2:
            self.send_thread = threading.Thread(target=self.send_messages)

    def start(self):
        self.receive_thread.start()
        if self.mode == 2:
            self.send_thread.start()
            self.send_thread.join()
        self.receive_thread.join()
        self.client_socket.close()

    def get_mode(self):
        mode = int(
            input(
                "Select Mode (1: Respond every N lines, 2: Respond every N seconds): "
            )
        )
        return mode

    def get_n(self):
        n = int(input(f"Enter N (lines for mode 1 or seconds for mode 2): "))
        return n

    def receive_messages(self):
        line_count = 0

        while True:
            if not self.connected:
                if not self.connect_and_register():
                    break
            try:
                message = receive_message(self.client_socket)
                if message is False:
                    print("Connection closed by the server")
                    self.connected = False
                    self.client_socket.close()
                    time.sleep(self.retry_delay)
                    continue

                self.conversation_log.append(message)
                print(sender_colored_message(*deserialize_message(message)))
                line_count += 1

                if self.mode == 1 and line_count >= self.n:
                    ai_response = ai_call(
                        self.conversation_log, SYSTEM_PROMPT_RESPOND, self.client_name
                    )
                    print(ai_response)
                    self.client_socket.sendall(encode_message(ai_response))
                    self.conversation_log.append(
                        serialize_message(self.client_name, ai_response)
                    )
                    line_count = 0

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
        last_response_time = time.time()

        while True:
            if not self.connected:
                if not self.connect_and_register():
                    break
            if time.time() - last_response_time >= self.n:
                ai_response = ai_call([], SYSTEM_PROMPT_DISRUPT, self.client_name)
                self.client_socket.sendall(encode_message(ai_response))
                print(ai_response)
                self.conversation_log.append(
                    serialize_message(self.client_name, ai_response)
                )
                last_response_time = time.time()


if __name__ == "__main__":
    ai_client = AIClient()
    ai_client.start()
