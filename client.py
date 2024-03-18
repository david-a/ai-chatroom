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


SERVER_HOST = "localhost"
SERVER_PORT = 8000


def receive_messages(client_socket, _client_name):
    while True:
        try:
            message = receive_message(client_socket)
            if message is False:
                print("Connection closed by the server")
                break

            print(sender_colored_message(*deserialize_message(message)))

        except Exception as e:
            print(f"Error receiving message: {e}")
            break


def send_messages(client_socket, _client_name):
    while True:
        message = input()
        if message:
            client_socket.sendall(encode_message(message))


if __name__ == "__main__":
    # Get the client name from command line argument or use a default name
    if len(sys.argv) > 1:
        client_name = sys.argv[1]
    else:
        client_name = f"Client-{generate_random_string()}"

    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    print(f"Connected to {SERVER_HOST}:{SERVER_PORT}")

    # Send the client name to the server
    client_socket.sendall(encode_message(client_name))

    # Start threads for sending and receiving messages
    receive_thread = threading.Thread(
        target=receive_messages, args=(client_socket, client_name)
    )
    send_thread = threading.Thread(
        target=send_messages, args=(client_socket, client_name)
    )

    receive_thread.start()
    send_thread.start()

    # Wait for threads to finish
    receive_thread.join()
    send_thread.join()

    # Close the socket
    client_socket.close()
