'''Test Client'''
import socket
import ssl
HOSTNAME = 'localhost'
PORT = 6023

context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
    with context.wrap_socket(sock, server_hostname=HOSTNAME) as ssock:
        print(ssock.version())
