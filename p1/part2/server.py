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


def pad(data):
    while len(data) % 4 != 0:
        data += b"\0"
    return data


def roundup(size):
    return ((size + 3) // 4) * 4


def validate_received_data(data, expected_payload_length=None):
    # Check data length is aligned on a 4-byte boundary
    if len(data) % 4 != 0:
        return False

    # Check minimum data length
    if len(data) < HEADER_SIZE:
        return False

    # Parse header
    payload_len, _, _, _ = struct.unpack("!IIH2s", data[:HEADER_SIZE])

    # Check if data length matches the specified length in header
    actual_payload_size = roundup(payload_len)
    if len(data) < HEADER_SIZE + actual_payload_size:
        return False

    # Check expected payload length
    if expected_payload_length is not None and payload_len != expected_payload_length:
        return False

    return True


def stage_a(client_socket, client_address, initial_data, student_id):
    # Verify the header and payload
    payload_len, psecret, step, _ = struct.unpack("!IIH2s", initial_data[:HEADER_SIZE])
    payload = initial_data[HEADER_SIZE:].decode("utf-8")

    if (
        not validate_received_data(initial_data)
        or payload_len != len(payload)
        or psecret != 0
        or step != STEP
        or payload != "hello world\0"
    ):
        print("Stage a: Invalid payload")
        client_socket.close()
        return None

    # Generate response
    num = random.randint(1, 100)
    length = random.randint(1, 100)
    udp_port = random.randint(1025, 65000)
    secretA = random.randint(1, 1000)

    response_payload = struct.pack("!IIII", num, length, udp_port, secretA)

    # Add header to the response
    header = generate_header(len(response_payload), 0, 2, student_id)
    response = pad(header + response_payload)

    client_socket.sendto(response, client_address)

    print("STAGE A COMPLETE")
    print("stage a output:", num, length, udp_port, secretA, "\n")

    return num, length, udp_port, secretA


def stage_b(num, length, udp_port, secretA, student_id):
    acked_packets = set()

    # Create new UDP socket bound to udp_port
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as new_socket:
        new_socket.settimeout(3)  # 3 seconds timeout
        new_socket.bind(("", udp_port))

        # Loop until we have acknowledged all expected packets
        while len(acked_packets) < num:
            try:
                data, client_address = new_socket.recvfrom(
                    HEADER_SIZE + roundup(length + 4)
                )

                if not validate_received_data(data, length + 4):
                    print("Stage b: Invalid payload")
                    new_socket.close()
                    return None

                _, psecret, step, _ = struct.unpack("!IIH2s", data[:HEADER_SIZE])

                # Verify the header
                if psecret != secretA or step != 1:
                    return None

                # Extract packet_id from the payload
                packet_id = struct.unpack("!I", data[HEADER_SIZE : HEADER_SIZE + 4])[0]

                # If the packet is as expected and not already acked
                if 0 <= packet_id < num and packet_id not in acked_packets:
                    acked_packets.add(packet_id)

                    # Send the ack
                    ack_payload = struct.pack("!I", packet_id)
                    header = generate_header(len(ack_payload), secretA, 1, student_id)
                    new_socket.sendto(pad(header + ack_payload), client_address)

            except socket.timeout:
                print(f"Stage b, port: {udp_port}: No data received for 3 seconds")
                continue

        # all packets have been acked, send the response
        tcp_port = random.randint(1025, 65000)
        secretB = random.randint(1, 1000)

        response_payload = struct.pack("!II", tcp_port, secretB)
        header = generate_header(len(response_payload), secretA, 2, student_id)
        new_socket.sendto(pad(header + response_payload), client_address)

        print("STAGE B COMPLETE")
        print("stage b output:", tcp_port, secretB, "\n")

        return tcp_port, secretB


def stage_c_d(secretB, tcp_port, student_id):
    # Create TCP socket and bind it to the tcp_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_tcp_socket:
        server_tcp_socket.bind(("", tcp_port))
        server_tcp_socket.listen(1)  # Allow 1 pending connection
        server_tcp_socket.settimeout(3)  # 3 seconds timeout

        conn, _ = server_tcp_socket.accept()

        try:
            with conn:
                # Generate values for num2, len2, secretC, and c
                num2 = random.randint(1, 10)
                len2 = random.randint(1, 10)
                secretC = random.randint(1, 1000)
                c = chr(random.randint(97, 122))  # a random lowercase letter

                # Pack the values into payload
                payload = struct.pack("!IIIc", num2, len2, secretC, c.encode())
                header = generate_header(len(payload), secretB, 2, student_id)
                conn.sendall(pad(header + payload))

                print("STAGE C COMPLETE")
                print("stage c output:", num2, len2, secretC, c, "\n")

                secretD = stage_d(secretC, num2, len2, c, conn, student_id)
                return secretC, secretD

        except socket.timeout:
            print(f"Stage c, port: {tcp_port}: No data received for 3 seconds")
            return None


def stage_d(secretC, num2, len2, c, conn, student_id):
    expected_payload = c.encode() * len2

    for _ in range(num2):
        data = conn.recv(HEADER_SIZE + roundup(len2))

        if not validate_received_data(data, len2):
            print("Stage d: Invalid payload")
            conn.close()
            return None

        data = data[HEADER_SIZE : HEADER_SIZE + len2]
        if data != expected_payload:
            print("Stage d: Invalid payload")
            conn.close()
            return None

    # secretD response
    secretD = random.randint(1, 1000)

    response_payload = struct.pack("!I", secretD)
    header = generate_header(len(response_payload), secretC, 2, student_id)
    conn.sendall(pad(header + response_payload))

    print("STAGE D COMPLETE")
    print("stage d output:", secretD, "\n")
    return secretD


def handle_client(client_socket, client_address, initial_data):
    try:
        _, _, _, student_id = struct.unpack("!IIH2s", initial_data[:HEADER_SIZE])

        # Stage A
        num, length, udp_port, secretA = stage_a(
            client_socket, client_address, initial_data, student_id
        )

        # Stage B
        tcp_port, secretB = stage_b(num, length, udp_port, secretA, student_id)

        # Stage C & D
        secretC, secretD = stage_c_d(secretB, tcp_port, student_id)

        print("secrets:", secretA, secretB, secretC, secretD, "\n")

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("0.0.0.0", PORT))
    print(f"Server listening on port {PORT}...")

    while True:
        try:
            initial_data, addr = server_socket.recvfrom(N_BYTES)
            print(f"Received data from {addr}:")
            client_thread = threading.Thread(
                target=handle_client, args=(server_socket, addr, initial_data)
            )
            client_thread.start()
        except Exception as e:
            print(f"Error while receiving data: {e}")


if __name__ == "__main__":
    main()
