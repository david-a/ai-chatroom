import errno
import hashlib
import random
import socket
import string
from colorama import Fore, Style
import time

HEADER_LENGTH = 10
SYSTEM_SENDER_NAME = "System"


def get_color_from_name(name):
    """
    Generates a consistent color for a given name using a hash function.
    """
    if name == SYSTEM_SENDER_NAME:
        return Fore.RED
    # Convert the name to bytes and hash it using SHA-256
    name_bytes = name.encode("utf-8")
    name_hash = hashlib.sha256(name_bytes).hexdigest()

    # Map the hash to a color using the hash value modulo the number of colors
    colors = [Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    color_index = int(name_hash, 16) % len(colors)
    color_code = colors[color_index]

    return color_code


def color_message(message, color):
    """
    Colors the message with the specified color.
    """
    return f"{color}{message}{Style.RESET_ALL}"


def sender_colored_message(sender_name, message_content):
    """
    Colors the message based on the sender's name.
    """

    sender_color = get_color_from_name(sender_name)

    return color_message(serialize_message(sender_name, message_content), sender_color)


def generate_random_string(length=5):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def get_message_length_from_header(header):
    """
    Extracts the message length from the header.
    """
    return int(header.decode("utf-8").strip())


def serialize_message(sender, message):
    return f"{sender}: {message}"


def deserialize_message(serialized_message):
    return serialized_message.split(": ")


def decode_message(message):
    """
    Decodes a message received from the server.
    """
    return message.decode("utf-8")


def encode_message(message):
    """
    Encodes a message to be sent to the server.
    """
    message_length = len(message)
    header = f"{message_length:<{HEADER_LENGTH}}".encode("utf-8")
    return header + message.encode("utf-8")


def receive_message(sckt):
    """
    Receives a message from the server.
    """
    max_retries = 3
    retry_delay = 1

    for i in range(max_retries):
        try:
            header = sckt.recv(HEADER_LENGTH)
            if not header:
                return False

            message = sckt.recv(get_message_length_from_header(header))

            return decode_message(message)
        except socket.error as e:
            if e.args[0] == errno.EAGAIN or e.args[0] == errno.EWOULDBLOCK:
                print(
                    "No data available." + " Retrying..." if i < max_retries - 1 else ""
                )
                time.sleep(retry_delay)
            else:
                # a "real" error occurred
                print(f"Error: {e}")
                return False

    return False
