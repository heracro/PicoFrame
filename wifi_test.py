import socket

udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
udp_socket.bind(("", 14440))  # Listen on the same port as the app

print("Listening for UDP broadcasts...")
while True:
    data, addr = udp_socket.recvfrom(1024)
    print(f"Received {data.decode()} from {addr}")
    udp_socket.sendto(b"RaspiFrame:192.168.100.156", addr)