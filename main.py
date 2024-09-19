import network
import socket
import time
import struct
import gc
import hub75
import random
from machine import Pin


HEIGHT = 64
WIDTH = 64
MAX_PIXELS = 64

h75 = hub75.Hub75(WIDTH, HEIGHT, stb_invert=False)

def connect_to_wifi(max_attempts=10):
    ssid = 'NDI_86'
    password = '09484108'
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

    duration_data = recv_exact(sock, 4)
    duration = struct.unpack('!f', duration_data)[0]

    pixels = bytearray()
    chunk_size = 256
    print(f"Free memory: {gc.mem_free()} bytes")
    counter = 0
    while True:
        try:
            for _ in range(chunk_size):
                pixel_data = recv_exact(sock, 4)
                if not pixel_data:
                    raise ValueError("Incomplete pixel data")
                pixels.extend(pixel_data)
                counter += 1
                print(pixel_data)
            gc.collect()  

        except ValueError:
            break

    print(counter)
    print(f"Free memory: {gc.mem_free()} bytes")

    del chosen_slot_data, duration_data, pixel_data
    gc.collect()  

    return chosen_slot, duration, pixels

def set_pixels(duration, pixels):
    index = 0
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if index + 4 <= len(pixels):
                r = pixels[index + 1]
                g = pixels[index + 2]
                b = pixels[index + 3]
                h75.set_pixel(x, y, r, g, b)
                print('Setting Pixel x: {0} y: {1}, with red: {2} green: {3} blue: {4}'.format(x, y, r, g, b))

                index += 4
    time.sleep(duration)

def main():
    ip_address = connect_to_wifi()
    if not ip_address:
        return
    Pin("LED", Pin.OUT).on()
    

    server_socket = setup_server(ip_address)
    client_socket, client_address = server_socket.accept()
    print('Connection from:', client_address)

    chosen_slot, duration, pixels = decode_data(client_socket)
    print(f"Chosen Slot: {chosen_slot}, Time: {duration}, Pixels: {pixels}")
    print(f"len(pixels): {len(pixels)}")
    
    set_pixels(duration, pixels)

    client_socket.close()
    server_socket.close()

if __name__ == "__main__":
    h75.start()

    main()