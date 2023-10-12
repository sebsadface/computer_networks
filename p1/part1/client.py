import socket

if __name__ == '__main__':
  url = "attu2.cs.washington.edu"
  port = 12235
  server_address = (url, )
  message = "hello world"

  socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  socket.connect((url, port))
  socket.sendto(message, server_address)
  socket.close(); 