import socket
import struct

n_bytes = 1024
url = "attu3.cs.washington.edu"
port = 12235
server_address = (url, port)

step = 1
student_id = 851

def create_header(message, psecret):
  header = b''

  header += len(message).to_bytes(4, byteorder='big')
  header += psecret.to_bytes(4, byteorder='big')
  header += step.to_bytes(2, byteorder='big')
  header += student_id.to_bytes(2, byteorder='big')

  return header

def stage_a():
  message = "hello world\0"

  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  header = create_header(message, 0)
  sock.sendto(header + message.encode(), server_address)

  response, address = sock.recvfrom(n_bytes)

  sock.close()
  return response

# def stage_b(a_response):

if __name__ == '__main__':
  a_response = stage_a()

  format_string = '>IIII'
  num, length, udp_port, secretA = struct.unpack(format_string, a_response[12:])

  print(num, length, udp_port, secretA)
  
  # stage_b(response_a)
  