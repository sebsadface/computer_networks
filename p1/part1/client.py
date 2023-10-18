import socket
import struct

n_bytes = 1024
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
  sock.settimeout(1)

  for i in range(num):
    retries = 10

    while retries > 0:
      try:
        header = create_header(length + 4, secretA)

        message = i.to_bytes(4, byteorder='big')
        message += bytes(length)
        message += bytes(length % 4)

        sock.sendto(header + message, server_address)

        response, _ = sock.recvfrom(n_bytes)
        print(response.hex())
        break

      except socket.timeout:
        retries -= 1
        print("retrying")
    else:
      raise Exception("No response received after all retries")
  
  b_response, _ = sock.recvfrom(n_bytes)
  sock.close()

  return b_response

def stage_c(tcp_port: int, secretB: int):
  server_address = (url, tcp_port)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  sock.connect(server_address)
  
  sock.close()
  return ''

if __name__ == '__main__':
  a_response = stage_a()
  num, length, udp_port, secretA = struct.unpack('>IIII', a_response[12:])

  print("stage a output")
  print(num, length, udp_port, secretA)

  b_response = stage_b(num, length, udp_port, secretA)
  tcp_port, secretB = struct.unpack('>II', b_response[12:])
  
  print("stage b output")
  print(tcp_port, secretB)

  c_reponse = stage_c(tcp_port, secretB)
