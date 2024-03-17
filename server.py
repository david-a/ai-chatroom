import socket
import select

from utils import encode_message, receive_message, SYSTEM_SENDER_NAME

SERVER_HOST = "localhost"
SERVER_PORT = 8000

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind the socket to the host and port
server_socket.bind((SERVER_HOST, SERVER_PORT))

# Listen for incoming connections
server_socket.listen()

# Keep track of connected clients and their sockets
sockets_list = [server_socket]
clients = {}

print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}")

while True:
    # Use select.select() to handle multiple connections
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            # Accept a new connection
            client_socket, client_address = server_socket.accept()
            client_socket.setblocking(False)
            sockets_list.append(client_socket)

            # Receive the client name
            try:
                client_name = receive_message(client_socket)
                clients[client_socket] = (client_address, client_name)
                print(
                    f"Accepted new connection from {client_address} (Client: {client_name})"
                )

                # # Send welcome message to the newly connected client
                welcome_message = (
                    f"{SYSTEM_SENDER_NAME}: Welcome to the chatroom, {client_name}!"
                )
                client_socket.sendall(encode_message(welcome_message))

            except BlockingIOError:
                # Handle the blocking error by skipping this client
                sockets_list.remove(client_socket)
                client_socket.close()
                print(
                    f"Connection from {client_address} failed due to a blocking error"
                )
                continue

        else:
            # Receive data from the client
            try:

                message = receive_message(notified_socket)
                if message is False:
                    # Client disconnected
                    sockets_list.remove(notified_socket)
                    del clients[notified_socket]
                    continue

                # Broadcast the message to all other clients
                client_address, client_name = clients[notified_socket]
                broadcast_message = f"{client_name}: {message}"
                encoded_message = encode_message(broadcast_message)
                for client_socket in clients:
                    if client_socket != notified_socket:
                        try:
                            client_socket.sendall(encoded_message)
                        except BlockingIOError:
                            # Handle the blocking error by skipping this client
                            sockets_list.remove(client_socket)
                            client_socket.close()
                            del clients[client_socket]
                            print(
                                f"Connection to {clients[client_socket][0]} failed due to a blocking error"
                            )

            except BlockingIOError:
                # Handle the blocking error by skipping this client
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                notified_socket.close()
                print(
                    f"Connection to {clients[notified_socket][0]} failed due to a blocking error"
                )
                continue

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
