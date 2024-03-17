import socket
import threading

SERVER_HOST = "localhost"
SERVER_PORT = 8000
HEADER_LENGTH = 10


def receive_messages(client_socket):
    while True:
        try:
            header = client_socket.recv(HEADER_LENGTH)
            if not header:
                print("Connection closed by the server")
                break

            message_length = int(header.decode("utf-8").strip())
            message = client_socket.recv(message_length)
            print(message.decode("utf-8"))

        except Exception as e:
            print(f"Error receiving message: {e}")
            break


def send_messages(client_socket):
    while True:
        message = input()
        if message:
            message_length = len(message)
            header = f"{message_length:<{HEADER_LENGTH}}".encode("utf-8")
            client_socket.sendall(header + message.encode("utf-8"))


# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect((SERVER_HOST, SERVER_PORT))
print(f"Connected to {SERVER_HOST}:{SERVER_PORT}")

# Start threads for sending and receiving messages
receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
send_thread = threading.Thread(target=send_messages, args=(client_socket,))

receive_thread.start()
send_thread.start()

# Wait for threads to finish
receive_thread.join()
send_thread.join()

# Close the socket
client_socket.close()
