import network
import socket
import time
import struct
import os

# Wi-Fi credentials
SSID = ''
PASSWORD = ''

def recv_exact(sock, num_bytes):
    """Receive the exact number of bytes from the socket."""
    data = b''
    while len(data) < num_bytes:
        packet = sock.recv(num_bytes - len(data))
        if not packet:
            break
        data += packet
    return data

def decode_data(sock):
    chosen_slot_data = recv_exact(sock, 4)
    chosen_slot = struct.unpack('!i', chosen_slot_data)[0]

    time_data = recv_exact(sock, 4)
    time = struct.unpack('!f', time_data)[0]

    pixels = []
    chunk_size = 1024
    while True:
        try:
            pixel_chunk = []
            for _ in range(chunk_size):
                pixel_data = recv_exact(sock, 4)
                pixel = struct.unpack('!i', pixel_data)[0]
                pixel_chunk.append(pixel)
            pixels.extend(pixel_chunk)
        except ValueError:
            break

    return chosen_slot, time, pixels


wlan = network.WLAN(network.STA_IF)
wlan.active(True)

wlan.connect(SSID, PASSWORD)

max_attempts = 10
attempts = 0
while not wlan.isconnected() and attempts < max_attempts:
    print('Connecting to Wi-Fi...')
    time.sleep(1)
    attempts += 1

if wlan.isconnected():
    print('Connected to Wi-Fi')
    ip_address = wlan.ifconfig()[0]
    print('IP Address:', ip_address)
else:
    print('Failed to connect to Wi-Fi')

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((ip_address, 14440))  # Bind to the IP address and port 12345
server_socket.listen(100)  # Listen for incoming connections

print('Waiting for a connection...')
client_socket, client_address = server_socket.accept()
print('Connection from:', client_address)

chosen_slot, time, pixels = decode_data(client_socket)
print(f"Chosen Slot: {chosen_slot}, Time: {time}, Pixels: {pixels}")
print(f"len(pixels): {len(pixels)}")

client_socket.close()
server_socket.close()