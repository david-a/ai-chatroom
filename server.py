import socket
import select

from lib.utils import (
    encode_message,
    receive_message,
    SYSTEM_SENDER_NAME,
    serialize_message,
)


class Server:
    def __init__(self, host="localhost", port=8000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.sockets_list = [self.server_socket]
        self.clients = {}
        print(f"Server is listening on {self.host}:{self.port}")

    def start(self):
        while True:
            read_sockets, _, exception_sockets = select.select(
                self.sockets_list, [], self.sockets_list
            )
            self.handle_sockets(read_sockets, exception_sockets)

    def handle_sockets(self, read_sockets, exception_sockets):
        for notified_socket in read_sockets:
            if notified_socket == self.server_socket:
                self.accept_new_connection(notified_socket)
            else:
                self.receive_and_broadcast_message(notified_socket)

        for notified_socket in exception_sockets:
            self.remove_client(notified_socket)

    def accept_new_connection(self, notified_socket):
        client_socket, client_address = notified_socket.accept()
        client_socket.setblocking(False)
        self.sockets_list.append(client_socket)

        try:
            client_name = receive_message(client_socket)
            self.clients[client_socket] = (client_address, client_name)
            print(
                f"Accepted new connection from {client_address} (Client: {client_name})"
            )

            welcome_message = serialize_message(
                SYSTEM_SENDER_NAME, f"Welcome to the chatroom, {client_name}!"
            )
            client_socket.sendall(encode_message(welcome_message))

        except BlockingIOError:
            self.sockets_list.remove(client_socket)
            client_socket.close()
            print(f"Connection from {client_address} failed due to a blocking error")

    def receive_and_broadcast_message(self, notified_socket):
        try:
            message = receive_message(notified_socket)
            if message is False:
                self.remove_client(notified_socket)
                return

            client_address, client_name = self.clients[notified_socket]
            broadcast_message = serialize_message(client_name, message)
            encoded_message = encode_message(broadcast_message)
            self.broadcast_to_clients(encoded_message, notified_socket)

        except BlockingIOError:
            self.remove_client(notified_socket)

    def broadcast_to_clients(self, encoded_message, sender_socket):
        for client_socket in self.clients:
            if client_socket != sender_socket:
                try:
                    client_socket.sendall(encoded_message)
                except BlockingIOError:
                    self.remove_client(client_socket)

    def remove_client(self, notified_socket):
        self.sockets_list.remove(notified_socket)
        client_address, client_name = self.clients[notified_socket]
        del self.clients[notified_socket]
        notified_socket.close()
        print(
            f"Connection to {client_address} (Client: {client_name}) failed due to a blocking error"
        )


if __name__ == "__main__":
    server = Server()
    server.start()
