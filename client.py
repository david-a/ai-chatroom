import hashlib
import socket
import threading
import sys
import random
import string
from colorama import Fore, Style


SERVER_HOST = "localhost"
SERVER_PORT = 8000
HEADER_LENGTH = 10


def get_color_from_name(name):
    """
    Generates a consistent color for a given name using a hash function.
    """
    # Convert the name to bytes and hash it using SHA-256
    name_bytes = name.encode("utf-8")
    name_hash = hashlib.sha256(name_bytes).hexdigest()

    # Map the hash to a color using the hash value modulo the number of colors
    colors = [
        Fore.RED,
        Fore.GREEN,
        Fore.YELLOW,
        Fore.BLUE,
        Fore.MAGENTA,
        Fore.CYAN,
        Fore.WHITE,
    ]
    color_index = int(name_hash, 16) % len(colors)
    color_code = colors[color_index]

    return color_code


def generate_random_string(length=5):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def receive_messages(client_socket, client_name):
    print(f"Welcome {client_name}!")
    while True:
        try:
            header = client_socket.recv(HEADER_LENGTH)
            if not header:
                print("Connection closed by the server")
                break

            message_length = int(header.decode("utf-8").strip())
            message = client_socket.recv(message_length)

            # Extract the sender name from the message
            sender_name, message_content = message.decode("utf-8").split(": ", 1)

            # Get the color for the sender using the mapping function
            sender_color = get_color_from_name(sender_name)

            # Color the message based on the sender
            colored_message = (
                f"{sender_color}{sender_name}: {message_content}{Style.RESET_ALL}"
            )
            print(colored_message)

        except Exception as e:
            print(f"Error receiving message: {e}")
            break


def send_messages(client_socket, _client_name):
    while True:
        message = input()
        if message:
            message_length = len(message)
            header = f"{message_length:<{HEADER_LENGTH}}".encode("utf-8")
            client_socket.sendall(header + message.encode("utf-8"))


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
    client_name_header = f"{len(client_name):<{HEADER_LENGTH}}".encode("utf-8")
    client_socket.sendall(client_name_header + client_name.encode("utf-8"))

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
