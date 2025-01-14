#!/usr/bin/env python3
import sys
import ipaddress
import json
import re
import getpass
import requests
from requests.exceptions import RequestException
from requests.auth import HTTPDigestAuth
import os

# Define color codes for logging
red_start = "\033[91m"  # ANSI code for Red text
amber_start = "\033[33m" # ANSI code for Amber text
lime_green_start = "\033[92m"
reset = "\033[0m"  # ANSI reset code

# ASCII Art definition
ascii_art = f"{lime_green_start}\n\n"\
    "   _____                      ____           \n"
    "  / ___/___  ____  ________  / __ \\_________ \n"
    "  \\__ \\/ _ \\/ __ \\/ ___/ _ \\/ /_/ / ___/ __ \\\n"
    " ___/ /  __/ / / (__  )  __/ ____/ /  / /_/ /\n"
    "/____/\\___/_/ /_/____/\\___/_/   /_/   \\____/ \n"
    "                                             V1      \n\n"
    "SensePro Wizard.\n\n"
    f"{reset}"  # Reset color

def create_env_file(nvr_user, nvr_password):
    # Define the location and name of your env file in the user's home directory
    env_file_path = os.path.expanduser('~/.SensePro_env')

    try:
        with open(env_file_path, 'w') as env_file:
            env_file.write(f'NVR_USERNAME={nvr_user}\n')
            env_file.write(f'NVR_PASSWORD={nvr_password}\n')
        print(f"Environment file created successfully at {env_file_path}")
    except IOError as e:
        print(f"Failed to create environment file: {e}")

def get_detector_ids(input_str):
    """Parse a string for individual or range of detector IDs."""
    detectors = set()
    for part in input_str.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            detectors.update(range(start, end + 1))
        else:
            detectors.add(int(part))
    return list(detectors)

def prompt_for_camera_selection(total_cameras):
    while True:
        selection = input("Would you like to connect all IP CCTV cameras to DuoSense? Type Y or Yes or select a range of cameras (For example 1-16 or 1,3,6,12 etc): ").lower()
        if selection in ['y', 'yes']:
            return list(range(1, total_cameras + 1))
        else:
            try:
                return get_detector_ids(selection)
            except ValueError:
                print(f"{red_start}I think something went wrong. Please enter a valid selection.{reset}")

#Check for valid IP address
def is_valid_ip(ip_addr):
    # Regular expression for validating an IPv4 address
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'

    # Split the IP address and port
    ip_parts = ip_addr.split(':')

    # Check if the IP part matches the IPv4 pattern
    if not re.match(ipv4_pattern, ip_parts[0]):
        return False

    # Validate the IP address part
    try:
        ip = ipaddress.ip_address(ip_parts[0])
        if type(ip) is not ipaddress.IPv4Address:
            return False
    except ValueError:
        return False

    # Validate port number if present
    if len(ip_parts) > 1:
        try:
            port = int(ip_parts[1])
            if port < 0 or port > 65535:
                return False
        except ValueError:
            return False

    return True

# Check the IP format and range
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    if re.match(pattern, ip_addr):
        parts = ip_addr.split(".")
        return all(0 <= int(part) <= 255 for part in parts)
    return False

def get_valid_ip(description, used_ips):
    while True:
        ip = input(f"\033[92mEnter IP address for {description}: \033[0m")
        if not is_valid_ip(ip):
            print("\033[91m\n\n""Invalid IP address format or range. Please enter a valid IP address (XXX.XXX.XXX.XXX), with each segment between 0-255.""\n\n\033[0m")
            continue

        if ip in used_ips and used_ips[ip] != description:
            print(f"I see you are using the same IP address for {used_ips[ip]}. Is this right?")
            confirm = input("If so, please specify the port number. If incorrect, type N or No: ")
            if confirm.lower() not in ["n", "no"]:
                port = input("Enter the port number: ")
                ip_with_port = f"{ip}:{port}"
                return ip_with_port
            else:
                continue

        used_ips[ip] = description
        return ip

# Updated GPIO layout template with device names
gpio_layout_template = [
    ("", "3V3", "1", "2", "5V", ""),
    ("", "GPIO 2", "3", "4", "5V", ""),
    ("", "GPIO 3", "5", "6", "Ground", ""),
    ("", "GPIO 4", "7", "8", "GPIO 14", ""),
    ("", "Ground", "9", "10", "GPIO 15", ""),
    ("", "GPIO 17", "11", "12", "GPIO 18", ""),
    ("", "GPIO 27", "13", "14", "Ground", ""),
    ("", "GPIO 22", "15", "16", "GPIO 23", ""),
    ("", "3V", "17", "18", "GPIO 24", ""),
    ("", "GPIO10", "19", "20", "Ground", ""),
    ("", "GPIO9", "21", "22", "GPIO 25", ""),
    ("", "GPIO 11", "23", "24", "GPIO 8", ""),
    ("", "Ground", "25", "26", "GPIO 7", ""),
    ("", "GPIO 0", "27", "28", "GPIO 1", ""),
    ("", "GPIO 5", "29", "30", "Ground", ""),
    ("", "GPIO 6", "31", "32", "GPIO 12", ""),
    ("", "GPIO 13", "33", "34", "Ground", ""),
    ("", "GPIO 19", "35", "36", "GPIO 16", ""),
    ("", "GPIO 26", "37", "38", "GPIO 20", ""),
    ("", "Ground", "39", "40", "GPIO 21", "")
]

# Function to format GPIO layout as a table with device names
def format_console_table_with_devices(data):
    # Define the table header
    header = ["Your Device", "BCM PIN", "Physical PIN", "Physical PIN", "BCM PIN", "Your Device"]

    # Find the maximum width of the data for formatting
    max_width = max(len(max([i for sub in data for i in sub], key=len)), len(header[1]))

    # Create the format string for each row of the table
    row_format = "{:<{width}} {:<{width}} {:<{width}} {:<{width}} {:<{width}} {:<{width}}".format

    # Initialize the table string with the header
    table_str = row_format(*header, width=max_width) + "\n"
    table_str += "-" * (max_width * len(header)) + "\n"

    # Print each row of data
    for row in data:
        table_str += row_format(*row, width=max_width) + "\n"

    return table_str

# Function to prompt for a GPIO pin and ensure it's not already used
def prompt_for_gpio(description, used_gpio_pins):
    restricted_gpio_pins = {0, 1, 2, 3}  # Set of restricted GPIO pins
    while True:
        try:
            pin = int(input(f"\033[92mEnter BCM (GPIO) pin for {description}: \033[0m"))
            if pin in restricted_gpio_pins:
                print(f"{red_start}BCM (GPIO) pin {pin} is restricted and cannot be used. Please choose a different pin."f"{reset}")
                continue  # Skip the rest of the loop and prompt for a new pin
            if pin in used_gpio_pins:
                print(f"{red_start}BCM (GPIO) pin {pin} is already in use. Please choose a different pin."f"{reset}")
            else:
                used_gpio_pins.add(pin)
                return pin
        except ValueError:
            print("Invalid input. Please enter a number.")

# BCM to physical pin mapping based on Raspberry Pi GPIO pinout
bcm_to_physical_pin = {
    2: 3,   # BCM GPIO2 is physical pin 3
    3: 5,   # BCM GPIO3 is physical pin 5
    4: 7,   # BCM GPIO4 is physical pin 7
    17: 11, # BCM GPIO17 is physical pin 11
    27: 13, # BCM GPIO27 is physical pin 13
    22: 15, # BCM GPIO22 is physical pin 15
    10: 19, # BCM GPIO10 is physical pin 19
    9: 21,  # BCM GPIO9 is physical pin 21
    11: 23, # BCM GPIO11 is physical pin 23
    0: 27,  # BCM GPIO0 is physical pin 27 (On some Pi models, this is GPIO ID_SD)
    5: 29,  # BCM GPIO5 is physical pin 29
    6: 31,  # BCM GPIO6 is physical pin 31
    13: 33, # BCM GPIO13 is physical pin 33
    19: 35, # BCM GPIO19 is physical pin 35
    26: 37, # BCM GPIO26 is physical pin 37
    14: 8,  # BCM GPIO14 is physical pin 8
    15: 10, # BCM GPIO15 is physical pin 10
    18: 12, # BCM GPIO18 is physical pin 12
    23: 16, # BCM GPIO23 is physical pin 16
    24: 18, # BCM GPIO24 is physical pin 18
    25: 22, # BCM GPIO25 is physical pin 22
    8: 24,  # BCM GPIO8 is physical pin 24
    7: 26,  # BCM GPIO7 is physical pin 26
    1: 28,  # BCM GPIO1 is physical pin 28 (On some Pi models, this is GPIO ID_SC)
    12: 32, # BCM GPIO12 is physical pin 32
    16: 36, # BCM GPIO16 is physical pin 36
    20: 38, # BCM GPIO20 is physical pin 38
    21: 40, # BCM GPIO21 is physical pin 40
}

def create_gpio_layout_with_devices(config):
    camera_pins = {bcm_to_physical_pin[camera_info["pin"]]: camera_name for camera_name, camera_info in config["ipcctv"].items()}
    detector_pins = {bcm_to_physical_pin[detector_info["pin"]]: detector_info["name"] for detector_id, detector_info in config["detectors"].items()}

    updated_gpio_layout_template = [list(row) for row in gpio_layout_template]

    for row in updated_gpio_layout_template[1:]:
        physical_pin_left = int(row[2]) if row[2].isdigit() else 0
        physical_pin_right = int(row[3]) if row[3].isdigit() else 0
        if physical_pin_left in camera_pins:
            row[0] = camera_pins[physical_pin_left]
        elif physical_pin_right in camera_pins:
            row[5] = camera_pins[physical_pin_right]
        if physical_pin_left in detector_pins:
            row[0] = detector_pins[physical_pin_left]
        elif physical_pin_right in detector_pins:
            row[5] = detector_pins[physical_pin_right]

    with open('gpio_layout.txt', 'w') as gpio_layout_file:
        gpio_layout_file.write(format_console_table_with_devices(updated_gpio_layout_template))

def handle_keyboard_interrupt():
    print(
        f"{lime_green_start}\n\n"
        "   _____                      ____           \n"
        "  / ___/___  ____  ________  / __ \\_________ \n"
        "  \\__ \\/ _ \\/ __ \\/ ___/ _ \\/ /_/ / ___/ __ \\\n"
        " ___/ /  __/ / / (__  )  __/ ____/ /  / /_/ /\n"
        "/____/\\___/_/ /_/____/\\___/_/   /_/   \\____/ \n"
        "                                             V1      \n\n"
        "SensePro Wizard has now aborted.\n\n"
        f"{reset}"
    )

def create_config():
    try:
        # Fetch camera names with authentication
        while True:
            nvr_ip = input("Enter the IP/Hostname[:port] of the NVR/IPC: ")
            if is_valid_ip(nvr_ip):
                break
            else:
                print("\033[91m\n\nInvalid IP address format or range. Please enter a valid IP address (XXX.XXX.XXX.XXX), with each segment between 0-255.\n\n\033[0m")

        nvr_user = input("Enter the NVR/IPC username for authentication: ")
        nvr_password = getpass.getpass("Enter the NVR/IPC password for authentication: ")

        # Try to make a network request
        response = requests.get(
            f'http://{nvr_ip}/cgi-bin/configManager.cgi?action=getConfig&name=ChannelTitle',
            auth=HTTPDigestAuth(nvr_user, nvr_password)
        )
        response.raise_for_status()

        # Process response to get camera names and count channels
        camera_names = []
        total_channels = 0
        for line in response.text.splitlines():
            if 'Name=' in line:
                total_channels += 1
                name = line.split('=')[1].strip()
                if not name.startswith('Channel'):
                    camera_names.append(name + " - IPC")

        print(f"{amber_start}DuoSense has detected you're using a {total_channels} Channel Network Video Recorder with {len(camera_names)} CCTV cameras connected.{reset}")
        print(f"{red_start}If you have more Channels, please ensure you have named your IPC's correctly and not used the default naming structure (for example Channel*).{reset}")

        # Prompt for camera selection
        selected_cameras = prompt_for_camera_selection(len(camera_names))

        # Print selected cameras
        print("Selected Cameras:")
        for i in selected_cameras:
            if i-1 < len(camera_names):
                print(f"{i}. {camera_names[i-1]}")
            else:
                print(f"{red_start}Warning: Camera ID {i} is not available.{reset}")

        # Call the function to create the env file with the credentials
        create_env_file(nvr_user, nvr_password)

        # Camera configuration
        used_ips = {}  # Initialize a dictionary to keep track of used IP addresses
        ipcctv = {}
        all_detector_ids = set()
        used_gpio_pins = set()  # Initialize a set to keep track of used GPIO pins

        for camera_index in selected_cameras:
            if camera_index-1 < len(camera_names):
                camera_name = camera_names[camera_index-1]
                ip = get_valid_ip(camera_name, used_ips)  # Now also passing used_ips
                pin = prompt_for_gpio(camera_name, used_gpio_pins)
                detectors = get_detector_ids(input(f"\033[92mEnter detector IDs for {camera_name} (Example 1,3,6 or a range 1-4): \033[0m"))
                ipcctv[camera_name] = {"ip": ip, "pin": pin, "name": camera_name, "detectors": detectors}
                all_detector_ids.update(detectors)
            else:
                print(f"{red_start}Warning: Camera ID {camera_index} is not available.{reset}")

        # Detector configuration
        print(f"\033[92mYou have {len(all_detector_ids)} detectors in total. Let's start by assigning your BCM (GPIO) pins.\033[0m")
        detectors = {}

        for detector_id in sorted(all_detector_ids):
            pin = prompt_for_gpio(f"detector {detector_id}", used_gpio_pins)
            name = input(f"\033[92mEnter name for detector {detector_id}: \033[0m")
            detectors[detector_id] = {"pin": pin, "name": name}

        # Time threshold
        time_threshold = int(input("\033[92mEnter time threshold in minutes for confirming intrusion: \033[0m"))

        # Create the configuration dictionary
        config = {
            "ipcctv": ipcctv,
            "detectors": detectors,
            "time_threshold": time_threshold
        }

        # Write to JSON file
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)

        # Create GPIO layout file with device names
        create_gpio_layout_with_devices(config)

        print("\033[92mConfiguration file created successfully.\033[0m")

    except KeyboardInterrupt:
        handle_keyboard_interrupt()
        sys.exit(1)

    except RequestException as e:
        print(f"{red_start}DuoSense failed to establish a connection. Please ensure that the NVR/IPC device at {nvr_ip} is online and reachable.Exiting.{reset}")
        sys.exit(1)

    except Exception as e:
        print(f"{red_start}An error occurred: {e}{reset}")
        sys.exit(1)

def main():
    # Print the ASCII Art at the very start
    print(ascii_art)

    # Start the configuration process
    create_config()

    # Add an exit message with a star border and in lime green
    message = "Configuration process completed. Exiting the application."
    padded_message = f"*  {message}  *"  # Add padding and stars to the message
    border_length = len(padded_message)
    border = f"{lime_green_start}{'*' * border_length}\n"

    print(f"\n{border}{padded_message}\n{border}{reset}")

    # Exit the script
    sys.exit(0)

if __name__ == "__main__":
    main()
    try:
        create_config()

    except KeyboardInterrupt:
        handle_keyboard_interrupt()
        sys.exit(1)

    except Exception as e:
        print(f"{red_start}An error occurred: {e}{reset}")
        sys.exit(1)
