from flask import Flask, request, jsonify
import socket
import threading
import os


app = Flask(__name__)

@app.route("/image", methods=["POST"])
def upload_image():
    """
    Endpoint to upload image data to a specific slot.
    Expects JSON payload with keys: slot, duration, pixels.
    """
    try:
        data = request.get_json()
        slot = data['slot']
        duration = data['duration']
        pixels = data['pixels']
        slots[slot] = {"duration": duration, "pixels": pixels}
        return jsonify({"status": "success", "slot": slot}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/image", methods=["GET"])
def get_image():
    """
    Endpoint to fetch image data for a specific slot.
    """
    slot = request.args.get("slot", type=int)
    if slot in slots:
        return jsonify(slots[slot]), 200
    else:
        return jsonify({"status": "error", "message": "Slot not found"}), 404


@app.route("/slots", methods=["GET"])
def get_slots():
    """
    Endpoint to list all slots and their statuses.
    """
    busy_slots = list(slots.keys())
    return jsonify({"slots": busy_slots}), 200


def set_pixels(duration, pixels):
    """
    Sets pixels on the virtual LED matrix or prints them for debugging.
    """
    index = 0
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if index + 3 < len(pixels):
                r = pixels[index]
                g = pixels[index + 1]
                b = pixels[index + 2]
                print(f'Setting Pixel x: {x}, y: {y}, red: {r}, green: {g}, blue: {b}')
                index += 3
    time.sleep(duration)


@app.route("/image/display", methods=["POST"])
def display_image():
    """
    Endpoint to display an image from a specific slot.
    """
    try:
        data = request.get_json()
        slot = data['slot']
        if slot not in slots:
            return jsonify({"status": "error", "message": "Slot not found"}), 404

        image_data = slots[slot]
        duration = image_data["duration"]
        pixels = image_data["pixels"]

        set_pixels(duration, pixels)
        return jsonify({"status": "success", "slot": slot}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/ping", methods=["GET", "POST"])
def ping():
    return jsonify({"status": "success", "message": "Received ping"}), 200



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
