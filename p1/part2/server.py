import socket

server_address = ("attu2.cs.washington.edu", 12235)

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listener.bind(server_address)

n_bytes = 1024

while True:
    try:
        connection, client_addr = listener.accept()
        try:
            connection.recv(n_bytes)
        finally:
            connection.close()
    except:
        listener.close()
