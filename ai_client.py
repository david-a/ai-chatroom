import socket
import threading
import time

from lib.ai_utils import ai_call
from lib.utils import (
    deserialize_message,
    encode_message,
    generate_random_string,
    receive_message,
    sender_colored_message,
    serialize_message,
)

SERVER_HOST = "localhost"
SERVER_PORT = 8000

SYSTEM_PROMPT_RESPOND = (
    "You are a joyful chat participant. respond in the context of the conversation."
)
SYSTEM_PROMPT_DISRUPT = (
    "You are a joyful chat participant. Initiate a conversation with a random sentence."
)


def receive_messages(client_socket, client_name, mode, n, conversation_log=[]):
    line_count = 0

    while True:
        try:
            message = receive_message(client_socket)
            if message is False:
                print("Connection closed by the server")
                break
            conversation_log.append(message)
            print(sender_colored_message(*deserialize_message(message)))
            line_count += 1

            if mode == 1 and line_count >= n:
                # Respond every N lines
                ai_response = ai_call(
                    conversation_log, SYSTEM_PROMPT_RESPOND, client_name
                )
                print(ai_response)
                client_socket.sendall(encode_message(ai_response))
                conversation_log.append(serialize_message(client_name, ai_response))
                line_count = 0  # reset line count after responding

        except Exception as e:
            print(f"Error receiving message: {e}")
            break


def send_messages(client_socket, client_name, n, conversation_log=[]):
    last_response_time = time.time()
    while True:
        if time.time() - last_response_time >= n:
            # Say something new and unrelated every N seconds
            ai_response = ai_call([], SYSTEM_PROMPT_DISRUPT, client_name)
            client_socket.sendall(encode_message(ai_response))
            print(ai_response)
            conversation_log.append(serialize_message(client_name, ai_response))
            last_response_time = time.time()


if __name__ == "__main__":
    client_name = f"AI-{generate_random_string()}"
    conversation_log = []
    mode = int(
        input("Select Mode (1: Respond every N lines, 2: Respond every N seconds): ")
    )
    n = int(input(f"Enter N (lines for mode 1 or seconds for mode 2): "))

    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    print(f"Connected to {SERVER_HOST}:{SERVER_PORT}")

    # Send the AI client name to the server
    client_socket.sendall(encode_message(client_name))

    # Only start receiving thread because send_messages is handled based on mode
    receive_thread = threading.Thread(
        target=receive_messages,
        args=(client_socket, client_name, mode, n, conversation_log),
    )
    receive_thread.start()

    # # No need for send_messages in mode 2 as it's handled within the receive_messages
    if mode == 2:
        send_thread = threading.Thread(
            target=send_messages,
            args=(client_socket, client_name, n, conversation_log),
        )
        send_thread.start()
        send_thread.join()

    receive_thread.join()
    client_socket.close()
