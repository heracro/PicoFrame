from flask import Flask
import socket
import threading
import os


app = Flask(__name__)


def start_udp_listener():
    """
    Listens for UDP broadcast messages and responds with device info.
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.bind(("", 14440))

    print("Listening for UDP broadcasts...")
    while True:
        data, addr = udp_socket.recvfrom(1024)
        message = data.decode()
        print(f"Received broadcast: {message} from {addr}")
        if message.startswith("RaspiFrame:"):
            response = f"RaspiFrame:{get_ip_address()}"
            udp_socket.sendto(response.encode(), addr)


def get_ip_address():
    """
    Gets the IP address of the device from the `hostname` command.
    """
    try:
        ip_address = os.popen('hostname -I').read().strip().split()[0]
        return ip_address
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return "127.0.0.1"

if __name__ == "__main__":
    listener_thread = threading.Thread(target=start_udp_listener, daemon=True)
    listener_thread.start()
    app.run(host="0.0.0.0", port=14440)
