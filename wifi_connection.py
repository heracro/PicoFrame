import network
import socket
import time
import struct
import gc

from rgbmatrix import RGBMatrix, RGBMatrixOptions



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

    time_data = recv_exact(sock, 4)
    time = struct.unpack('!f', time_data)[0]

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
            gc.collect()  # Trigger garbage collection more frequently

        except ValueError:
            break

    print(counter)
    print(f"Free memory: {gc.mem_free()} bytes")

    # Free memory by deleting large objects
    del chosen_slot_data, time_data, pixel_data
    gc.collect()  # Trigger garbage collection after deleting objects

    return chosen_slot, time, pixels

def print_memory_info():
    gc.collect()
    print(f"Free memory: {gc.mem_free()} bytes")
    print(f"Allocated memory: {gc.mem_alloc()} bytes")
    print(f"Total memory: {gc.mem_free() + gc.mem_alloc()} bytes")


def main():
    print_memory_info()
    ip_address = connect_to_wifi()
    print_memory_info()
    if not ip_address:
        return
    print_memory_info()
    server_socket = setup_server(ip_address)
    client_socket, client_address = server_socket.accept()
    print('Connection from:', client_address)
    print_memory_info()
    chosen_slot, time, pixels = decode_data(client_socket)
    print_memory_info()
    print(f"Chosen Slot: {chosen_slot}, Time: {time}, Pixels: {pixels}")
    print(f"len(pixels): {len(pixels)}")
    
    client_socket.close()
    server_socket.close()


if __name__ == "__main__":
    main()
