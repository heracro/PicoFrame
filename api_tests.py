import requests
import json


class RaspberryPiClient:
    def __init__(self, ip, port):
        """
        Initialize the client with the Raspberry Pi's IP and port.
        :param ip: IP address of the Raspberry Pi
        :param port: Port number where the Flask server is running
        """
        self.base_url = f"http://{ip}:{port}"

    def send_request(self, endpoint, method="GET", data=None):
        """
        Generic method to send an HTTP request to the Raspberry Pi.
        :param endpoint: API endpoint to call (e.g., '/system')
        :param method: HTTP method ('GET', 'POST', etc.)
        :param data: Data to send with the request (for POST/PUT requests)
        :return: Response JSON or error message
        """
        url = f"{self.base_url}{endpoint}"
        print(f"Sending {method} request to {url}")
        try:
            if method == "GET":
                response = requests.get(url, params=data)
            elif method == "POST":
                response = requests.post(url, json=data)
            else:
                return f"Unsupported HTTP method: {method}"

            # Handle response
            if response.status_code == 200:
                return response.json()  # Return parsed JSON
            else:
                return {
                    "error": f"Request failed with status {response.status_code}",
                    "details": response.text,
                }
        except Exception as e:
            return {"error": str(e)}

    def check_memory(self):
        """
        Check the memory status of the Raspberry Pi using the /system endpoint with 'getFreeMem' action.
        :return: Parsed memory status or error message
        """
        return self.send_request("/system", method="POST", data={"action": "getfreemem"})

    def update_raspiframe(self):
        """
        Update the RaspiFrame application on the Raspberry Pi.
        :return: Response JSON or error message
        """
        return self.send_request("/system", method="POST", data={"action": "update_raspiframe"})

    def update_raspbian(self):
        """
        Update the Raspbian OS on the Raspberry Pi.
        :return: Response JSON or error message
        """
        return self.send_request("/system", method="POST", data={"action": "update_raspbian"})

    def reboot(self):
        """
        Reboot the Raspberry Pi.
        :return: Response JSON or error message
        """
        return self.send_request("/system", method="POST", data={"action": "reboot"})

    def shutdown_raspiframe(self):
        """
        Shut down the RaspiFrame application.
        :return: Response JSON or error message
        """
        return self.send_request("/system", method="POST", data={"action": "shutdown"})

    def get_busy_slots(self):
        """
        Fetch the list of busy slots from the Raspberry Pi.
        :return: List of busy slots or an error message
        """
        return self.send_request("/slots", method="GET")

    def clear_slot(self, slot_number):
        """
        Test clearing a specific slot using the /slots/clear endpoint.
        """
        return self.send_request("/slots/clear", method="POST", data={"slot": slot_number})

    def get_image(self, slot):
        """
        Retrieve image data from a specific slot on the Raspberry Pi.
        :param slot: Slot number to fetch the image data from.
        :return: Image data JSON or an error message
        """
        return self.send_request("/image", method="GET", data={"slot": slot})

    def display_image(self, image_data):
        """
        Send image data to the Raspberry Pi for display.
        :param image_data: Dictionary containing image data.
        :return: Response JSON or error message.
        """
        return self.send_request("/display_image", method="POST", data=image_data)


def load_image_data_from_json(file_path):
    """
    Load image data from a JSON file.
    :param file_path: Path to the JSON file containing image data.
    :return: Parsed JSON data or an error message.
    """
    try:
        with open(file_path, "r") as file:
            raw_data = file.read()
            raw_data = raw_data.lstrip("\ufeff")
            print("Raw file content:", raw_data)
            data = json.loads(raw_data.encode('utf-8').decode('utf-8'))
            print(f"Loaded image data from {file_path}.")
            return data
    except Exception as e:
        print(f"Failed to load image data from {file_path}: {e}")
        return None


if __name__ == "__main__":
    raspberry_pi_ip = "192.168.100.156"
    raspberry_pi_port = 14440
    slot = '1'
    json_file_path = "test_image_data.json"
    client = RaspberryPiClient(raspberry_pi_ip, raspberry_pi_port)
    # print("Checking memory status...")
    # print(client.check_memory())
    # print("Updating RaspiFrame...")
    # print(client.update_raspiframe())
    # print(client.update_raspbian())
    # print("Rebooting Raspberry Pi...")
    # print(client.reboot())
    # print("Shutting down RaspiFrame...")
    # print(client.shutdown_raspiframe())
    # print("Fetching busy slots...")
    # print(client.get_busy_slots())
    # print(f"Fetching image from slot {slot}...")
    # print(client.get_image(slot))
    # image_data = load_image_data_from_json(json_file_path)
    # if image_data:
    #     print("Sending image data to the Raspberry Pi for display...")
    #     response = client.display_image(image_data)
    #     print("Response from Raspberry Pi:", response)
    print("Clearing slot...")
    print(client.clear_slot(slot))