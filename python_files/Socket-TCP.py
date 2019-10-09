import socket

'''
Short program to experiment on sending TCP packets to a router and receiving replies from it
Requires router to act as HTTP server
This program must be run as superuser
'''

ROUTER_INT_IP = '222.222.1.1'
PORT = 80
MTU = 1500


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print("Hello World")
    s.connect((ROUTER_INT_IP, PORT))
    print("Hello World 2")
    s.sendall(b'GET / HTTP/1.1\r\nHost: 222.222.1.1\r\n\r\n')
    print("Hello World 3")
    data = s.recv(MTU)
    print("Hello World 4")
    s.close()
    print("Hello World 5")

print("\nMessage received was:\n")
print(data.decode('utf-8'))
