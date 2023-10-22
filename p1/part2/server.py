import socket
import threading
import struct
import random

N_BYTES = 1024
PORT = 12235
STUDENT_ID = 851


def stage_b(udp_socket, num, length, udp_port):
    received_packets = {}

    while len(received_packets) < num:
        data, addr = udp_socket.recvfrom(N_BYTES)

        # Verify the header and payload
        payload_len, psecret, step, student_num = struct.unpack("!IIH2s", data[:12])
        packet_id = struct.unpack("!I", data[12:16])[0]
        payload = data[16:]

        if (
            payload_len != len(payload) + 4
            or len(payload) != length
            or packet_id in received_packets
            or step != 1
        ):
            return None

        received_packets[packet_id] = True

        # Send acknowledgment for the received packet
        ack = struct.pack("!I", packet_id)
        udp_socket.sendto(ack, addr)

        # Randomly decide not to send an acknowledgment at least once
        if len(received_packets) == num - 1 and random.choice([True, False]):
            return None

    # All packets received. Send TCP port and secretB
    tcp_port = random.randint(1025, 65000)
    secretB = random.randint(1, 1000)
    response = struct.pack("!II", tcp_port, secretB)
    udp_socket.sendto(response, addr)

    return tcp_port, secretB


def stage_c(tcp_port, secretB):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(("0.0.0.0", tcp_port))
    tcp_socket.listen(1)

    client_conn, addr = tcp_socket.accept()

    # Verify header (basic check for now)
    data = client_conn.recv(12)
    payload_len, psecret, step, student_num = struct.unpack("!IIH2s", data)

    if psecret != secretB or step != 1:
        client_conn.close()
        return None

    # Send data for stage C
    num2 = random.randint(1, 100)
    len2 = random.randint(1, 100)
    secretC = random.randint(1, 1000)
    c = chr(random.randint(97, 122))  # a random lowercase letter

    response = struct.pack("!IIIB", num2, len2, secretC, ord(c))
    client_conn.send(response)

    return client_conn, num2, len2, secretC, c


def stage_d(client_conn, num2, len2, char_c, secretC):
    for _ in range(num2):
        data = client_conn.recv(len2)

        # Verify payload length and content
        if len(data) != len2 or not all([byte == ord(char_c) for byte in data]):
            client_conn.close()
            return None

    # Send secretD after receiving all payloads
    secretD = random.randint(1, 1000)
    response = struct.pack("!I", secretD)
    client_conn.send(response)

    client_conn.close()
    return secretD


def handle_client(client_socket, client_address):
    try:
        # STAGE A
        data, addr = client_socket.recvfrom(N_BYTES)

        # Verify the header and payload
        payload_len, psecret, step, student_num = struct.unpack("!IIH2s", data[:12])
        payload = data[12:].decode("utf-8").rstrip("\0")

        if (
            payload_len != len(payload)
            or psecret != 0
            or step != 1
            or payload != "hello world"
        ):
            client_socket.close()
            return

        # Respond to client for stage A
        num = random.randint(1, 100)
        length = random.randint(1, 100)
        udp_port = random.randint(1025, 65000)
        secretA = random.randint(1, 1000)

        response = struct.pack("!IIII", num, length, udp_port, secretA)
        client_socket.sendto(response, client_address)

        # STAGE B
        udp_socket_for_b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket_for_b.bind(("0.0.0.0", udp_port))
        tcp_port, secretB = stage_b(udp_socket_for_b, num, length, udp_port)
        udp_socket_for_b.close()

        # STAGE C
        client_conn, num2, len2, secretC, char_c = stage_c(tcp_port, secretB)

        # STAGE D
        secretD = stage_d(client_conn, num2, len2, char_c, secretC)

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("0.0.0.0", PORT))
    print(f"Server listening on port {PORT}...")

    while True:
        _, addr = server_socket.recvfrom(
            1
        )  # We just need this to detect a client. Actual data will be handled in the thread.
        client_thread = threading.Thread(
            target=handle_client, args=(server_socket, addr)
        )
        client_thread.start()


if __name__ == "__main__":
    main()
