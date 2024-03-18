import unittest
from unittest.mock import patch
import string
from lib.utils import (
    HEADER_LENGTH,
    SYSTEM_SENDER_NAME,
    color_message,
    decode_message,
    deserialize_message,
    encode_message,
    generate_random_string,
    get_color_from_name,
    get_message_length_from_header,
    receive_message,
    sender_colored_message,
    serialize_message,
)


class TestUtils(unittest.TestCase):
    def test_get_color_from_name_system_sender(self):
        with patch("lib.utils.Fore") as mock_fore:
            color = get_color_from_name(SYSTEM_SENDER_NAME)
            self.assertEqual(color, mock_fore.RED)

    def test_get_color_from_name(self):
        with patch("lib.utils.Fore") as mock_fore:
            # Mock the hashlib.sha256 function to always return the same hash value
            with patch("lib.utils.hashlib.sha256") as mock_sha256:
                mock_sha256.return_value.hexdigest.return_value = "abcdef"
                color = get_color_from_name("John Doe")
                self.assertEqual(color, mock_fore.GREEN)

    def test_color_message(self):
        with patch("lib.utils.Style.RESET_ALL") as mock_reset_all:
            message = "Hello, World!"
            color = "MyColor"
            expected_result = f"{color}{message}{mock_reset_all}"
            result = color_message(message, color)
            self.assertEqual(result, expected_result)

    def test_sender_colored_message(self):
        sender_name = "John Doe"
        message_content = "Hello, World!"

        with patch("lib.utils.serialize_message") as mock_serialize_message, patch(
            "lib.utils.color_message"
        ) as mock_color_message, patch(
            "lib.utils.get_color_from_name"
        ) as mock_get_color_from_name:

            mock_serialize_message.return_value = "Serialized Message"
            mock_color_message.return_value = "Colored Message"
            mock_get_color_from_name.return_value = "Color"

            sender_colored_message(sender_name, message_content)

            mock_serialize_message.assert_called_once_with(sender_name, message_content)
            mock_color_message.assert_called_once_with("Serialized Message", "Color")
            mock_get_color_from_name.assert_called_once_with(sender_name)

    def test_generate_random_string(self):
        length = 5
        random_string = generate_random_string(length)
        self.assertEqual(len(random_string), length)
        self.assertTrue(
            all(c in string.ascii_letters + string.digits for c in random_string)
        )

    def test_get_message_length_from_header(self):
        header = b"   10\r\n"
        result = get_message_length_from_header(header)
        self.assertEqual(result, 10)

    def test_serialize_message(self):
        sender = "John Doe"
        message = "Hello, World!"
        expected_result = "John Doe: Hello, World!"
        result = serialize_message(sender, message)
        self.assertEqual(result, expected_result)

    def test_deserialize_message(self):
        serialized_message = "key: value"
        result = deserialize_message(serialized_message)
        self.assertEqual(result, ["key", "value"])

    def test_decode_message(self):
        message = b"Hello, World!"
        result = decode_message(message)
        self.assertEqual(result, "Hello, World!")

    def test_encode_message(self):
        message = "Hello, World!"
        expected_header = b"13        "
        expected_message = b"Hello, World!"
        result = encode_message(message)
        self.assertEqual(result[:HEADER_LENGTH], expected_header)
        self.assertEqual(result[HEADER_LENGTH:], expected_message)

    def test_receive_message(self):
        # Mock the socket.recv function to return a header and message
        with patch("socket.socket") as mock_socket, patch(
            "lib.utils.decode_message"
        ) as mock_decode_message, patch(
            "lib.utils.get_message_length_from_header"
        ) as mock_get_message_length_from_header:
            mock_socket.recv.side_effect = [
                b"   25\r\n",  # Mock header
                b"Hello, World!",  # Mock message
            ]
            mock_get_message_length_from_header.return_value = 25
            mock_decode_message.return_value = "Hello, World!"

            result = receive_message(mock_socket)
            mock_get_message_length_from_header.assert_called_with(b"   25\r\n")
            mock_socket.recv.assert_called_with(25)
            mock_decode_message.assert_called_with(b"Hello, World!")

            self.assertEqual(result, "Hello, World!")

    def test_receive_message_no_header(self):
        # Mock the socket.recv function to return an empty header
        with patch("socket.socket") as mock_socket:
            mock_socket.recv.return_value = b""
            result = receive_message(mock_socket)
            mock_socket.recv.assert_called_with(HEADER_LENGTH)

            self.assertEqual(result, False)


if __name__ == "__main__":
    unittest.main()
