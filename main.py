from flask import Flask, request, jsonify
import socket
import threading
import os
import time
import struct
import gc
import psutil
import zlib
import json

app = Flask(__name__)

SLOTS_FILE = "slots_data.json"
slots = {}


@app.route("/system", methods=["POST"])
def system_action():
    """
    Handle system-level actions like updating, rebooting, and shutting down.
    """
    try:
        data = request.get_json()
        print(f"data: {data}")
        action = data.get("action", "").lower()

        if action == "getfreemem":

            memory = psutil.virtual_memory()
            response = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percentage": memory.percent
            }
            return jsonify(response), 200

        elif action == "update_raspiframe":
            try:
                os.system("sudo systemctl restart raspiframe.service")
                return jsonify({"status": "success", "message": "RaspiFrame updated and restarted successfully"}), 200
            except Exception as e:
                return jsonify({"status": "error", "message": f"Failed to update RaspiFrame: {str(e)}"}), 500
        elif action == "update_raspbian":
            try:
                os.system("sudo apt-get update && sudo apt-get upgrade -y")
                return jsonify({"status": "success", "message": "Raspbian updated successfully"}), 200
            except Exception as e:
                return jsonify({"status": "error", "message": f"Failed to update Raspbian: {str(e)}"}), 500
        elif action == "reboot":
            try:
                os.system("sudo reboot")
                return jsonify({"status": "success", "message": "Rebooting Raspberry Pi..."}), 200
            except Exception as e:
                return jsonify({"status": "error", "message": f"Failed to reboot: {str(e)}"}), 500
        elif action == "shutdown":
            try:
                os.system("sudo shutdown now")
                return jsonify({"status": "success", "message": "Shutting down Raspberry Pi..."}), 200
            except Exception as e:
                return jsonify({"status": "error", "message": f"Failed to shut down: {str(e)}"}), 500
        else:
            return jsonify({"error": "Invalid action"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def initialize_slots(file_path="slots_data.json", number_of_slots=6):
    """
    Initialize the slots.json file with None values for all slots if it's empty or invalid.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if "slots" in data and isinstance(data["slots"], dict):
                print("Slots file is already initialized.")
                return  
    except (FileNotFoundError, json.JSONDecodeError):
        print("Slots file not found or invalid. Initializing with default slots.")

    default_slots = {str(i): None for i in range(number_of_slots)}

    with open(file_path, 'w') as f:
        json.dump({"slots": default_slots}, f, indent=4)

    print("Slots file has been initialized.")


def load_slots():
    """Load slots data from the JSON file."""
    number_of_slots = 6
    try:
        with open(SLOTS_FILE, 'r') as f:
            data = json.load(f)
            slots = data.get("slots", {})
            return slots
    except (FileNotFoundError, json.JSONDecodeError):
        print("Slots file not found or invalid")
        return slots
    

def save_slot(slot_number, slot_data, file_path="slots_data.json"):
    """
    Update a specific slot's value in the slots.json file.
    
    Args:
        slot_number (int): The slot number to update.
        slot_data (dict or None): The data to assign to the slot (e.g., image details or None).
        file_path (str): Path to the slots.json file.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        if "slots" not in data or not isinstance(data["slots"], dict):
            print("Invalid slots.json structure.")

        data["slots"][str(slot_number)] = slot_data
        print(f"Slot {slot_number} updated with data: {slot_data}")

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            print("Slots successfully saved.")

    except (FileNotFoundError, json.JSONDecodeError):
        print("Slots file not found or invalid.")
    except Exception as e:
        print(f"Failed to update slot {slot_number}: {e}")


@app.route("/slots", methods=["GET"])
def get_slots():
    """
    Endpoint to list all slots and their statuses.
    """
    print(f"Request: {request}")
    data = request.args
    slots = load_slots()
    print(f"slots: {slots}")
    print(f"len(slots):{len(slots)}")

    busy_slots = [key for key,value in slots.items() if value is not None]
    print(f"busy_slots: {busy_slots}")
    return jsonify({"slots": slots}), 200


def calculate_crc(image):
    """
    Calculates the CRC32 of the given image data.
    This replicates the behavior of the Java CRC calculation.
    
    Args:
        image (list of int): The image data as a list of integers (e.g., ARGB values).

    Returns:
        int: The calculated CRC32 value.
    """
    byte_data = bytearray()
    for value in image:
        byte_data.extend(value.to_bytes(4, byteorder='big', signed=True))
    
    crc32_value = zlib.crc32(byte_data) & 0xFFFFFFFF  
    return crc32_value


@app.route("/image", methods=["POST"])
def set_image():
    """
    Endpoint to upload image data to a specific slot.
    Expects JSON payload with keys: slot, duration, pixels.
    """
    try:
        data = request.get_json()
        print(f"image_data: {data}")
        if not data:
            return jsonify({"status": "error", "message": "Invalid payload"}), 400

        if "slot" not in data:
            return jsonify({"status": "error", "message": "Invalid payload, slot not in data"}), 400
        if "duration" not in data:
            return jsonify({"status": "error", "message": "Invalid payload, duration not in data"}), 400
        if "pixels" not in data:
            return jsonify({"status": "error", "message": "Invalid payload, pixels not in data"}), 400
        if "crc" not in data:
            return jsonify({"status": "error", "message": "Invalid payload, crc not in data"}), 400

        slot = data['slot']
        duration = data['duration']
        pixels = data['pixels']
        received_crc = data["crc"]
        
        calculated_crc = calculate_crc(pixels)
        if calculated_crc != received_crc:
            return jsonify({"message": "CRC mismatch", "expected_crc": calculated_crc, "status": "error"}), 400

        slots = load_slots()
        print(f"Current slots before update: {slots}")
        slots[slot] = {"duration": duration, "pixels": pixels, "crc": received_crc}
        save_slot(slot, slots[slot])
        print(f"Updated slots after setting image: {slots}")
        
        return jsonify({"status": "success","crc": calculated_crc, "slot": slot}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/image", methods=["GET"])
def get_image():
    """
    Endpoint to fetch image data for a specific slot.
    """
    slots = load_slots()

    slot = request.args.get("slot", type=str)
    if slot is None:
        return jsonify({"status":"error", "message":"Missing 'slot' parameter"}), 400
    print(f"Slot in get_image: {slot}")
    slot_data = slots.get(slot)
    print(f"Slots in get_image: {slots}")
    print(f"len(slots) in get_image:{len(slots)}")

    print(f"Requested slot_data in get_image: {slot_data}")
    if slot_data is None:
        return jsonify({"status":"error", "message":f"Slot {slot} is empty or does not exist"}), 400
    
    response_data = {
        "slot": slot,
        "duration": slot_data["duration"],
        "pixels": slot_data["pixels"],
        "crc": slot_data["crc"]
    }
    print(f"response_data: {response_data}")
    return jsonify(response_data), 200

@app.route("/reset", methods=["POST"])
def reset_slots():
    """Endpoint to reset all slots."""
    global slots
    slots = {i: None for i in range(6)}  
    save_slots()
    return jsonify({"message": "All slots reset", "status": "success"}), 200


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
    initialize_slots()
    listener_thread = threading.Thread(target=start_udp_listener, daemon=True)
    listener_thread.start()
    app.run(host="0.0.0.0", port=14440)
