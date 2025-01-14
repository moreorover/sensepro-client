#!/usr/bin/env python3
import os
import gpiozero
import requests
from requests.exceptions import ConnectionError
import logging
import time
from requests.auth import HTTPDigestAuth
from datetime import datetime, timedelta
import json
import argparse
import threading

# ANSI Color codes for logging
red_start = "\033[91m"  # ANSI code for Red text
amber_start = "\033[33m" # ANSI code for Amber text
lime_green_start = "\033[92m" # ANSI code for Lime Green text
cyan_start = "\033[36m" # ANSI code for Cyan text
cyan_bg_black_text = "\033[30m\033[46m" # ANSI code for Black text on Cyan background
yellow_bg_black_text = "\033[30m\033[43m" # ANSI code for Black text on Yellow background
red_bg_bold_white_text = "\033[41m\033[1m\033[37m" # ANSI code for bold white text on red background
green_bg_bold_white_text = "\033[42m\033[1m\033[37m" # ANSI code for bold white text on green background
reset = "\033[0m"  # ANSI reset code

# Set up argument parser for command-line options
parser = argparse.ArgumentParser()
parser.add_argument("--test-mode", help="Activate test mode", action="store_true")
args = parser.parse_args()

# Set TEST_MODE based on the command-line argument
TEST_MODE = args.test_mode

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

# Get the path to the .env file
env_file_path = os.path.join(script_dir, 'SensePro_env.env')

# Load environment variables
def load_env_variables(env_file_path):
    """Load environment variables from a file."""
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as file:
            for line in file:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    else:
        logging.error(f"{red_bg_bold_white_text}Environment file {env_file_path} not found.{reset}")

load_env_variables(env_file_path)

# Construct the path to the config.json file
config_file_path = os.path.join(script_dir, 'config.json')

# Load configuration from config.json file
if not os.path.exists(config_file_path):
    logging.error(f"{red_start}Config file not found at {config_file_path}.{reset}")
    exit(1)

try:
    with open(config_file_path, 'r') as config_file:
        config = json.load(config_file)
except KeyError as e:
    logging.error(f"{red_start}Missing key in config data: {e}{reset}")
    exit(1)
except json.JSONDecodeError as e:
    logging.error(f"{red_start}Error decoding JSON: {e}{reset}")
    exit(1)

# Extract configurations from config.json file
IPCCTV = config['ipcctv']
DETECTORS = config['detectors']
TIME_THRESHOLD = timedelta(minutes=config['time_threshold'])
ARM_DISARM_PIN = config['system_settings']['arm_disarm_pin']
COUNTDOWN_DURATION = config['system_settings']['countdown_duration']

# Initialize GPIO for arming/disarming using the pin from the configuration
arm_disarm_button = gpiozero.Button(ARM_DISARM_PIN, pull_up=True, bounce_time=0.5)
armed = False

# Initialize a flag to check if countdown is in progress
countdown_in_progress = False

# Function to disable event callbacks for all GPIO inputs
def disable_event_callbacks():
    for camera_info in IPCCTV.values():
        camera_info['device'].when_pressed = None
    for detector_info in DETECTORS.values():
        detector_info['device'].when_pressed = None

# Function to enable event callbacks for all GPIO inputs
def enable_event_callbacks():
    for camera_name, camera_info in IPCCTV.items():
        camera_info['device'].when_pressed = lambda name=camera_name: on_camera_triggered(name)
    for detector_id, detector_info in DETECTORS.items():
        detector_info['device'].when_pressed = lambda id=detector_id: on_detector_triggered(id)

# Function to fetch NVR state whether it is Armed or Disarmed based on NO NC
def fetch_nvr_state(nvr_info):
    url = f"http://{nvr_info['ip']}/cgi-bin/configManager.cgi?action=getConfig&name=Alarm[0].SensorType"
    try:
        response = requests.get(url, auth=HTTPDigestAuth(USER, PASSWORD))
        if response.status_code == 200:
            # Parse the response which might look like 'table.Alarm[0].SensorType=NC'
            # Assuming the format is consistent as 'table.Alarm[0].SensorType=VALUE'
            current_state = response.text.split('=')[-1].strip()
            logging.info(f"Current NVR state from {nvr_info['ip']} is {current_state}")
            return current_state
        else:
            logging.error(f"Failed to fetch NVR state from {nvr_info['ip']}. Status Code: {response.status_code}")
    except ConnectionError:
        logging.error(f"Unable to communicate with NVR at {nvr_info['ip']}.")
    except Exception as e:
        logging.error(f"Error when fetching NVR state from {nvr_info['ip']}: {e}")

    return None

# Set system state based on NVR status
    if armed:
        enable_event_callbacks()
    else:
        disable_event_callbacks()
    logging.info("System state initialized based on NVR configuration.")

# Function to reset the last triggered times for all cameras and detectors
def reset_trigger_times():
    for camera_info in IPCCTV.values():
        camera_info['last_triggered'] = None
    for detector_info in DETECTORS.values():
        detector_info['last_triggered'] = None

# Arm Function
def arm_system():
    global armed, countdown_in_progress
    if not countdown_in_progress and not armed:
        logging.info(f"{red_bg_bold_white_text}Arming system...{reset}")
        countdown_in_progress = True
        disable_event_callbacks()  # Disable triggers during countdown
        reset_trigger_times()  # Reset all last triggered times to ensure a clean state
        for remaining in range(COUNTDOWN_DURATION, 0, -1):
            logging.info(f"{red_start}System arms in {remaining} seconds...{reset}")
            time.sleep(1)
            if not countdown_in_progress:
                logging.info(f"{red_start}Arming interrupted.{reset}")
                enable_event_callbacks()  # Re-enable if interrupted
                return
        armed = True
        enable_event_callbacks()  # Re-enable after arming
        logging.info(f"{lime_green_start}System armed.{reset}")
        countdown_in_progress = False
        set_nvr_alarm_state("arm")
    else:
        if armed:
            logging.info(f"{red_start}System is already armed.{reset}")
        if countdown_in_progress:
            logging.info(f"{red_start}Arming process is already in progress.{reset}")

#Disarm Function
def disarm_system():
    global armed, countdown_in_progress
    if armed or countdown_in_progress:
        logging.info(f"{amber_start}Disarming system...{reset}")
        countdown_in_progress = False
        armed = False
        # Clear last triggered times
        for camera_info in IPCCTV.values():
            camera_info['last_triggered'] = None
        for detector_info in DETECTORS.values():
            detector_info['last_triggered'] = None
        logging.info(f"{lime_green_start}System disarmed.{reset}")
        set_nvr_alarm_state("disarm")
    else:
        logging.info(f"{red_bg_bold_white_text}System is already disarmed or no arming in progress.{reset}")

def set_nvr_alarm_state(mode):
    for nvr_id, nvr_info in config["NVRs"].items():
        ip = nvr_info["ip"]
        action = nvr_info[mode]
        input = action["input"]
        relay = action["relay"]
        logging.info(f"{amber_start}Setting NVR {nvr_id} alarm state to {relay} for mode {mode} at IP {ip}{reset}")
        change_nvr_alarm_state(ip, input, relay, USER, PASSWORD, nvr_id)

# Assign your arm and disarm functions directly to the button events.
arm_disarm_button.when_pressed = arm_system
arm_disarm_button.when_released = disarm_system

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

# Get the path to the .env file
env_file_path = os.path.join(script_dir, 'SensePro_env.env')

# Load environment variables
load_env_variables(env_file_path)

# Construct the path to the config.json file
config_file_path = os.path.join(script_dir, 'config.json')

# Check if the config.json file exists
if not os.path.exists(config_file_path):
    logging.error(
        f"{red_start}\n\n"  # Two line spaces above the message, start red color
        "SensePro Error: The 'config.json' file is not found in the expected directory.\n"
        "Please make sure that you have run the 'SensePro_Wizard' prior to this script.\n"
        "Ensure that the 'config.json' file is located in the same directory as the 'SensePro' script."
        f"\n\n{reset}"  # Two line spaces below the message, reset color
    )
    exit(1)

# Load configuration from config.json file
config_file_path = os.path.join(script_dir, 'config.json')
if not os.path.exists(config_file_path):
    logging.error(f"{red_start}Config file not found at {config_file_path}.{reset}")
    exit(1)

try:
    with open(config_file_path, 'r') as config_file:
        config = json.load(config_file)
    ARM_DISARM_PIN = config['system_settings']['arm_disarm_pin']
    COUNTDOWN_DURATION = config['system_settings']['countdown_duration']
except KeyError as e:
    logging.error(f"{red_start}Missing key in config data: {e}{reset}")
    exit(1)
except json.JSONDecodeError as e:
    logging.error(f"{red_start}Error decoding JSON: {e}{reset}")
    exit(1)

# Extract configurations from config.json file
IPCCTV = config['ipcctv']
DETECTORS = config['detectors']
TIME_THRESHOLD = timedelta(minutes=config['time_threshold'])
ARM_DISARM_PIN = config['system_settings']['arm_disarm_pin']
COUNTDOWN_DURATION = config['system_settings']['countdown_duration']

# Initialise 'last_triggered' for each camera and detector
for camera_info in IPCCTV.values():
    camera_info['last_triggered'] = None

for detector_info in DETECTORS.values():
    detector_info['last_triggered'] = None

# Create a new directory for logs
logs_dir = os.path.join(script_dir, 'logs')
os.makedirs(logs_dir, exist_ok=True)  # Create 'logs' directory if it doesn't exist

# Get the current date and time for the timestamp
current_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

# Define the log file path with a timestamp within the 'logs' directory
log_file_path = os.path.join(logs_dir, f'SensePro_{current_time}.log')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path, mode='a'),  # File handler to write logs to a file
        logging.StreamHandler()
    ]
)

# Accessing the environment variables
USER = os.getenv('NVR_USERNAME', 'default_username')
PASSWORD = os.getenv('NVR_PASSWORD', 'default_password')

# Function to change IPC alarm input state
def change_camera_alarm_state(camera_ip, sensor_state, user, password, camera_name):
    relay_channel = 0  # Assuming Relay_channel is 0 for all IP CCTV Cameras
    url = f"http://{camera_ip}/cgi-bin/configManager.cgi?action=setConfig&Alarm[{relay_channel}].SensorType={sensor_state}"
    try:
        response = requests.get(url, auth=HTTPDigestAuth(user, password))
        if response.status_code == 200:
            logging.info(f"Alarm state set to {sensor_state} for camera at {camera_ip}.")
        else:
            logging.error(f"Failed to set alarm state for camera at {camera_ip}. Status Code: {response.status_code}, Response: {response.text}")
    except ConnectionError:
        logging.error(f"Unable to communicate with camera {camera_name} at {camera_ip}.")
    except Exception as e:
        logging.error(f"Error when changing alarm state for camera at {camera_ip}: {e}")

# Change NVR alarm input state
def change_nvr_alarm_state(ip, input, relay, user, password, nvr_id):
    url = f"http://{ip}/cgi-bin/configManager.cgi?action=setConfig&{input}={relay}"
    try:
        response = requests.get(url, auth=HTTPDigestAuth(user, password))
        if response.status_code == 200:
            logging.info(f"{amber_start}Alarm state set to {relay} for NVR {nvr_id} at {ip}.{reset}")
        else:
            logging.error(f"Failed to set alarm state for NVR at {ip}. Status Code: {response.status_code}, Response: {response.text}")
    except ConnectionError:
        logging.error(f"Unable to communicate with NVR at {ip}.")
    except Exception as e:
        logging.error(f"Error when changing alarm state for NVR at {ip}: {e}")

# Trigger IPC alarm input
def send_alarm_to_camera(camera_ip, camera_name):
    if TEST_MODE:
        logging.info(f"{lime_green_start}Test Mode ON - Alarm not sent to {camera_name} at {camera_ip}{reset}")
    else:
        change_camera_alarm_state(camera_ip, "NO", USER, PASSWORD, camera_name)  # Change to NO state
        time.sleep(2)  # Wait for 2 seconds
        change_camera_alarm_state(camera_ip, "NC", USER, PASSWORD, camera_name)  # Change back to NC state

# Detector trigger function
def on_detector_triggered(detector_id):
    global countdown_in_progress
    if countdown_in_progress:
        return  # Ignore the trigger if countdown is in progress

    detector_id_str = str(detector_id)
    detector_name = DETECTORS[detector_id_str]["name"]
    logging.info(f"{yellow_bg_black_text}Detector {detector_name} triggered{reset}")
    DETECTORS[detector_id_str]["last_triggered"] = datetime.now()
    check_for_confirmed_intrusion()

# Camera trigger function
def on_camera_triggered(camera_id):
    global countdown_in_progress
    if countdown_in_progress:
        return  # Ignore the trigger if countdown is in progress

    camera_ip = IPCCTV[camera_id]["ip"]
    logging.info(f"{cyan_bg_black_text}{camera_id} - {camera_ip} triggered{reset}")
    IPCCTV[camera_id]["last_triggered"] = datetime.now()
    check_for_confirmed_intrusion()

#Check for confirmed intrusion
def check_for_confirmed_intrusion():
    current_time = datetime.now()
    for camera_id, camera in IPCCTV.items():
        if camera["last_triggered"]:
            for detector_id in camera["detectors"]:
                detector = DETECTORS.get(str(detector_id))
                if detector and detector["last_triggered"]:
                    time_difference = abs(camera["last_triggered"] - detector["last_triggered"])
                    logging.info(f"Time difference for {camera_id} and detector {detector_id}: {time_difference}")

                    if time_difference <= TIME_THRESHOLD:
                        logging.info(f"{red_bg_bold_white_text}Confirmed intrusion detected by {camera_id} and detector {detector_id}{reset}")
                        send_alarm_to_camera(camera["ip"], camera_id)
                        camera["last_triggered"] = None
                        detector["last_triggered"] = None
                        break

# Initialize GPIO for cameras
for camera_name, camera_info in IPCCTV.items():
    camera_info["device"] = gpiozero.Button(camera_info["pin"], pull_up=True, bounce_time=0.2)
    camera_info["device"].when_pressed = lambda name=camera_name: on_camera_triggered(name)

# Initialize GPIO for detectors
for detector_id, detector_info in DETECTORS.items():
    detector_info["device"] = gpiozero.Button(detector_info["pin"], pull_up=True, bounce_time=0.2)
    detector_info["device"].when_pressed = lambda id=detector_id: on_detector_triggered(id)

# Initialize system state based on NVR configuration
def initialize_system_state(config):
    global armed
    armed = False
    for nvr_name, nvr_info in config["NVRs"].items():
        nvr_current_state = fetch_nvr_state(nvr_info)
        if nvr_current_state:
            if nvr_current_state == nvr_info['arm']['relay']:
                armed = True
                logging.info(f"{nvr_name} at {nvr_info['ip']} is armed (SensorType: {nvr_current_state}).")
            elif nvr_current_state == nvr_info['disarm']['relay']:
                armed = False
                logging.info(f"{nvr_name} at {nvr_info['ip']} is disarmed (SensorType: {nvr_current_state}).")
            else:
                logging.warning(f"Unknown NVR state ({nvr_current_state}) for {nvr_name} at {nvr_info['ip']}.")

# Main operational loop
def main_loop():
    try:
        logging.info(
            f"{cyan_start}{'Test mode is active.' if TEST_MODE else 'Running in normal mode. Use --test-mode to activate test mode.'}\n\n"
            f"{reset}{lime_green_start}System is now running. Press CTRL+C to exit.{reset}\n\n"
            "   _____                      ____           \n"
            "  / ___/___  ____  ________  / __ \\_________ \n"
            "  \\__ \\/ _ \\/ __ \\/ ___/ _ \\/ /_/ / ___/ __ \\\n"
            " ___/ /  __/ / / (__  )  __/ ____/ /  / /_/ /\n"
            "/____/\\___/_/ /_/____/\\___/_/   /_/   \\____/ \n"
            "                                             V1\n\n"
        )
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.info(f"{lime_green_start}SensePro has been manually stopped. Exiting.{reset}")

# Main entry point
if __name__ == "__main__":
    load_env_variables()
    config_file_path = os.path.join(script_dir, 'config.json')
    if not os.path.exists(config_file_path):
        logging.error("Configuration file missing, ensure it's present.")
        sys.exit(1)
    try:
        with open(config_file_path) as file:
            config = json.load(file)
            initialize_system_state(config)  # Initialize system based on the NVR state
        main_loop()  # Start the main operational loop
    except Exception as e:
        logging.error(f"Failed to start the system: {str(e)}")
        sys.exit(1)
