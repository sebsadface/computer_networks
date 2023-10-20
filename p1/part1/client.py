import socket
import struct

n_bytes = 1024
HEADER_SIZE = 12
url = "attu3.cs.washington.edu"

step = 1
student_id = 851

def create_header(packet_len: int, psecret: int):
  header = packet_len.to_bytes(4, byteorder='big')
  header += psecret.to_bytes(4, byteorder='big')
  header += step.to_bytes(2, byteorder='big')
  header += student_id.to_bytes(2, byteorder='big')

  return header

def stage_a():
  port = 12235
  server_address = (url, port)
  message = "hello world\0"

  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  header = create_header(len(message), 0)
  sock.sendto(header + message.encode(), server_address)

  response, _ = sock.recvfrom(n_bytes)

  sock.close()
  return response

def stage_b(num: int, length: int, udp_port: int, secretA: int):
  server_address = (url, udp_port)
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.settimeout(0.5)

  for i in range(num):
    retries = 15

    while retries > 0:
      try:
        header = create_header(length + 4, secretA)

        message = i.to_bytes(4, byteorder='big')
        message += bytes(length)
        message += bytes(4 - (len(message) % 4))

        sock.sendto(header + message, server_address)

        response, _ = sock.recvfrom(n_bytes)
        print("ack", response.hex())
        break

      except socket.timeout:
        retries -= 1
        print("retrying")
    else:
      raise Exception("No response received after all retries")
  
  b_response, _ = sock.recvfrom(n_bytes)
  sock.close()

  return b_response

def stage_c(sock: socket):
  c_reponse = sock.recv(n_bytes)

  return c_reponse

def stage_d(sock: socket, num2: int, len2: int, secretC: int, c: bytes):
  header = create_header(len2, secretC)
  message = bytes(c * len2)
  if len(message) % 4 != 0:
    message += bytes(4 - (len(message) % 4))
  
  for _ in range(num2):
    sock.sendall(header + message)

  d_reponse = sock.recv(n_bytes)
 
  return d_reponse

if __name__ == '__main__':
  print("STAGE A")
  a_response = stage_a()
  num, length, udp_port, secretA = struct.unpack('>IIII', a_response[HEADER_SIZE:])
  print("stage a output", num, length, udp_port, secretA, "\n")

  print("STAGE B")
  b_response = stage_b(num, length, udp_port, secretA)
  tcp_port, secretB = struct.unpack('>II', b_response[HEADER_SIZE:])
  print("stage b output", tcp_port, secretB, "\n")

  # Connect to TCP socket
  server_address = (url, tcp_port)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  sock.connect(server_address)
  sock.settimeout(1)

  print("STAGE C")
  c_response = stage_c(sock)
  num2, len2, secretC, c = struct.unpack('>IIIc', c_response[HEADER_SIZE : HEADER_SIZE + 13])
  print("stage c output", num2, len2, secretC, c, "\n")

  print("STAGE D")
  d_response = stage_d(sock, num2, len2, secretC, c)
  sock.close()

  secretD = int.from_bytes(d_response[HEADER_SIZE:], byteorder='big')
  print("stage d output", secretD, "\n")
  
  print("secrets:", secretA, secretB, secretC, secretD)
