import requests


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
        try:
            if method == "GET":
                response = requests.get(url)
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


if __name__ == "__main__":
    # Replace with the actual IP and port of your Raspberry Pi
    raspberry_pi_ip = "192.168.100.156"  # Replace with the Pi's IP
    raspberry_pi_port = 14440           # Replace with the Flask server's port

    # Initialize the client
    client = RaspberryPiClient(raspberry_pi_ip, raspberry_pi_port)
    # Example: Check memory status
    print("Checking memory status...")
    print(client.check_memory())
    # print("Updating RaspiFrame...")
    # print(client.update_raspiframe())
    # print(client.update_raspbian())
    # print("Rebooting Raspberry Pi...")
    # print(client.reboot())
    # print("Shutting down RaspiFrame...")
    # print(client.shutdown_raspiframe())
