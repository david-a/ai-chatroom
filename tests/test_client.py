import unittest
from unittest.mock import patch
from io import StringIO
import socket
import threading
import sys
import random
import string
from colorama import Fore, Style
from client import (
    get_color_from_name,
    generate_random_string,
    receive_messages,
    send_messages,
)


class TestClient(unittest.TestCase):
    def test_get_color_from_name(self):
        name = "John"
        expected_color = Fore.BLUE
        color = get_color_from_name(name)
        self.assertEqual(color, expected_color)

    def test_generate_random_string(self):
        length = 5
        random_string = generate_random_string(length)
        self.assertEqual(len(random_string), length)

    @patch("sys.stdout", new_callable=StringIO)
    def test_receive_messages(self, mock_stdout):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_name = "Client1"
        # Mock the server response
        server_response = "Server: Welcome to the chatroom!"
        with patch("socket.recv", return_value=server_response.encode("utf-8")):
            receive_messages(client_socket, client_name)
        # Add assertions to check the expected output
        self.assertEqual(mock_stdout.getvalue().strip(), server_response)

    @patch("sys.stdin", StringIO("message\n"))
    def test_send_messages(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_name = "Client1"
        # Mock the server response
        server_response = "Server: Message received!"
        with patch("socket.sendall") as mock_sendall:
            with patch("socket.recv", return_value=server_response.encode("utf-8")):
                send_messages(client_socket, client_name)
        # Add assertions to check the expected behavior
        mock_sendall.assert_called_once_with("message\n".encode("utf-8"))

        # Uncomment the following line to check the expected output
        # self.assertEqual(mock_stdout.getvalue().strip(), server_response)


if __name__ == "__main__":
    unittest.main()
