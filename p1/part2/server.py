import socket
import threading
import struct
import random

N_BYTES = 1024
PORT = 12235
HEADER_SIZE = 12
STEP = 1


def generate_header(payload_length, psecret, step, student_id):
    return struct.pack("!IIH2s", payload_length, psecret, step, student_id)


def stage_a(client_socket, client_address, initial_data, student_id):
    # Verify the header and payload
    payload_len, psecret, step, _ = struct.unpack("!IIH2s", initial_data[:HEADER_SIZE])
    payload = initial_data[HEADER_SIZE:].decode("utf-8")

    if (
        payload_len != len(payload)
        or psecret != 0
        or step != STEP
        or payload != "hello world\0"
    ):
        print("Stage a: Invalid payload")
        return None

    # Generate the response for stage A
    num = random.randint(1, 100)
    length = random.randint(1, 100)
    udp_port = random.randint(1025, 65000)
    secretA = random.randint(1, 1000)

    response_payload = struct.pack("!IIII", num, length, udp_port, secretA)

    # Add the header to the response
    header = generate_header(len(response_payload), 0, 2, student_id)
    response = header + response_payload

    client_socket.sendto(response, client_address)

    return (num, secretA, udp_port)


def stage_b(secretA, num, student_id, udp_port):
    acked_packets = set()

    # Create a new UDP socket bound to udp_port
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as new_socket:
        new_socket.settimeout(3)  # 3 seconds timeout
        new_socket.bind(("", udp_port))

        # Loop until we have acknowledged all expected packets
        while len(acked_packets) < num:
            try:
                data, client_address = new_socket.recvfrom(N_BYTES)
                _, psecret, step, _ = struct.unpack("!IIH2s", data[:HEADER_SIZE])

                # Verify the header
                if psecret != secretA or step != 1:
                    return None

                # Extract packet_id from the payload
                packet_id = struct.unpack("!I", data[HEADER_SIZE : HEADER_SIZE + 4])[0]

                # If the packet is as expected and not already acknowledged
                if 0 <= packet_id < num and packet_id not in acked_packets:
                    acked_packets.add(packet_id)

                    # Send the acknowledgment
                    ack_payload = struct.pack("!I", packet_id)
                    header = generate_header(len(ack_payload), secretA, 1, student_id)
                    new_socket.sendto(header + ack_payload, client_address)

            except socket.timeout:
                continue

        # Once all packets have been acknowledged, send the response for stage B
        tcp_port = random.randint(1025, 65000)
        secretB = random.randint(1, 1000)

        response_payload = struct.pack("!II", tcp_port, secretB)
        header = generate_header(len(response_payload), secretA, 2, student_id)
        new_socket.sendto(header + response_payload, client_address)

        return tcp_port, secretB


def stage_c(secretB, tcp_port, student_id):
    # Create a TCP socket and bind it to the tcp_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_tcp_socket:
        server_tcp_socket.bind(("", tcp_port))
        server_tcp_socket.listen(1)  # Allow 1 pending connection

        conn, _ = server_tcp_socket.accept()
        with conn:
            # Generate values for num2, len2, secretC, and c
            num2 = random.randint(1, 10)
            len2 = random.randint(1, 10)
            secretC = random.randint(1, 1000)
            c = chr(random.randint(97, 122))  # a random lowercase letter

            # Pack the values into a payload
            payload = struct.pack("!IIIc", num2, len2, secretC, c.encode())
            header = generate_header(len(payload), secretB, 2, student_id)
            conn.sendall(header + payload)

            return num2, len2, secretC, c


def stage_d(secretC, num2, len2, c, conn, student_id):
    expected_payload = c.encode() * len2
    for _ in range(num2):
        data = conn.recv(len2)
        if data != expected_payload:
            return None  # Terminate if any payload doesn't match the expected format

    # After validating all received payloads, send the secretD response
    secretD = random.randint(1, 1000)
    response_payload = struct.pack("!I", secretD)
    header = generate_header(len(response_payload), secretC, 2, student_id)
    conn.sendall(header + response_payload)

    return secretD


def handle_client(client_socket, client_address, initial_data):
    try:
        _, _, _, student_id = struct.unpack("!IIH2s", initial_data[:HEADER_SIZE])

        # Stage A
        num, secretA, udp_port = stage_a(
            client_socket, client_address, initial_data, student_id
        )

        # Stage B
        tcp_port, secretB = stage_b(secretA, num, student_id, udp_port)

        # Stage C
        num2, len2, secretC, c = stage_c(secretB, tcp_port, student_id)

        # Stage D
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_tcp_socket:
            server_tcp_socket.bind(("", tcp_port))
            server_tcp_socket.listen(1)
            conn, _ = server_tcp_socket.accept()
            with conn:
                secretD = stage_d(secretC, num2, len2, c, conn, student_id)

        print(f"Secret D: {secretD}")

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("0.0.0.0", PORT))
    print(f"Server listening on port {PORT}...")

    while True:
        initial_data, addr = server_socket.recvfrom(N_BYTES)
        print(f"Received data from {addr}")
        client_thread = threading.Thread(
            target=handle_client, args=(server_socket, addr, initial_data)
        )
        client_thread.start()


if __name__ == "__main__":
    main()
