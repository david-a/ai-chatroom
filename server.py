import socket
import select

SERVER_HOST = "localhost"
SERVER_PORT = 8000
HEADER_LENGTH = 10

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
            clients[client_socket] = client_address
            print(f"Accepted new connection from {client_address}")

        else:
            # Receive data from the client
            try:
                header = notified_socket.recv(HEADER_LENGTH)
                if not header:
                    # Client disconnected
                    sockets_list.remove(notified_socket)
                    del clients[notified_socket]
                    continue

                message_length = int(header.decode("utf-8").strip())
                message = notified_socket.recv(message_length)

                # Broadcast the message to all other clients
                for client_socket in clients:
                    if client_socket != notified_socket:
                        client_socket.sendall(header + message)

            except Exception as e:
                print(f"Error handling client: {e}")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
