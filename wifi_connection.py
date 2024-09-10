import network
import socket
import time
import struct

SSID = ''
PASSWORD = ''


def connect_to_wifi(ssid, password, max_attempts=10):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    attempts = 0
    while not wlan.isconnected() and attempts < max_attempts:
        print('Connecting to Wi-Fi...')
        time.sleep(1)
        attempts += 1

    if wlan.isconnected():
        print('Connected to Wi-Fi')
        return wlan.ifconfig()[0]
    else:
        print('Failed to connect to Wi-Fi')
        return None


def setup_server(ip_address, port=14440, backlog=100):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ip_address, port))
    server_socket.listen(backlog)
    print('Waiting for a connection...')
    return server_socket


def recv_exact(sock, num_bytes):
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


def main():
    ip_address = connect_to_wifi(SSID, PASSWORD)
    if not ip_address:
        return

    server_socket = setup_server(ip_address)
    client_socket, client_address = server_socket.accept()
    print('Connection from:', client_address)

    chosen_slot, time, pixels = decode_data(client_socket)
    print(f"Chosen Slot: {chosen_slot}, Time: {time}, Pixels: {pixels}")
    print(f"len(pixels): {len(pixels)}")

    client_socket.close()
    server_socket.close()


if __name__ == "__main__":
    main()
