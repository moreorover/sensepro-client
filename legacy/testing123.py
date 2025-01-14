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

# ANSI Color codes for logging
red_start = "\033[91m"  # ANSI code for Red text
amber_start = "\033[33m"  # ANSI code for Amber text
lime_green_start = "\033[92m"  # ANSI code for Lime Green text
cyan_start = "\033[36m"  # ANSI code for Cyan text
yellow_start = "\033[93m"  # ANSI code for Yellow text
cyan_bg_black_text = "\033[30m\033[46m"  # ANSI code for Black text on Cyan background
yellow_bg_black_text = "\033[30m\033[43m"  # ANSI code for Black text on Yellow background
red_bg_bold_white_text = "\033[41m\033[1m\033[37m"  # ANSI code for bold white text on red background
green_bg_bold_white_text = "\033[42m\033[1m\033[37m"  # ANSI code for bold white text on green background
pink_bg_black_text = "\033[30m\033[45m"  # ANSI code for Black text on Pink background
pink_text = "\033[95m"  # ANSI code for Pink (magenta) text
reset = "\033[0m"  # ANSI reset code

# Set up argument parser for command-line options
parser = argparse.ArgumentParser()
parser.add_argument("--test-mode", help="Activate test mode", action="store_true")
args = parser.parse_args()

# Set TEST_MODE based on the command-line argument
TEST_MODE = args.test_mode

# Logging setup
script_dir = os.path.dirname(os.path.realpath(__file__))
logs_dir = os.path.join(script_dir, 'logs')
os.makedirs(logs_dir, exist_ok=True)  # Create 'logs' directory if it doesn't exist

current_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
log_file_path = os.path.join(logs_dir, f'SensePro_{current_time}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path, mode='a'),
        logging.StreamHandler()
    ]
)

# Load environment variables
def load_env_variables(env_file_path):
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as file:
            for line in file:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    else:
        logging.error(f"{red_bg_bold_white_text}Environment file {env_file_path} not found.{reset}")

env_file_path = os.path.join(script_dir, 'SensePro_env.env')
load_env_variables(env_file_path)

# Accessing the environment variables
USER = os.getenv('NVR_USERNAME', 'default_username')
PASSWORD = os.getenv('NVR_PASSWORD', 'default_password')

# Load configuration from config.json file
def load_configuration(config_file_path):
    if not os.path.exists(config_file_path):
        logging.error(f"{red_start}Config file not found at {config_file_path}.{reset}")
        exit(1)

    try:
        with open(config_file_path, 'r') as config_file:
            config = json.load(config_file)
            # Initialize last_triggered key for cameras and detectors
            for camera_info in config['ipcctv'].values():
                camera_info['last_triggered'] = None
            for detector_info in config['detectors'].values():
                detector_info['last_triggered'] = None
        return config
    except KeyError as e:
        logging.error(f"{red_start}Missing key in config data: {e}{reset}")
        exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"{red_start}Error decoding JSON: {e}{reset}")
        exit(1)

config_file_path = os.path.join(script_dir, 'config.json')
config = load_configuration(config_file_path)

# Extract configurations from config.json file
IPCCTV = config['ipcctv']
DETECTORS = config['detectors']
TIME_THRESHOLD = timedelta(minutes=config['time_threshold'])
ARM_DISARM_PIN = config['system_settings']['arm_disarm_pin']
COUNTDOWN_DURATION = config['system_settings']['countdown_duration']

# Initialize GPIO for arming/disarming using the pin from the configuration
arm_disarm_button = gpiozero.Button(ARM_DISARM_PIN, pull_up=True, bounce_time=0.5)
armed = False
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

# Function to reset the last triggered times for all cameras and detectors
def reset_trigger_times():
    for camera_info in IPCCTV.values():
        camera_info['last_triggered'] = None
    for detector_info in DETECTORS.values():
        detector_info['last_triggered'] = None

# Function to handle immediate arming without countdown
def arm_system_immediately():
    global armed, countdown_in_progress
    if not armed:
        logging.info(f"{red_bg_bold_white_text}Immediate arming without countdown.{reset}")
        armed = True
        disable_event_callbacks()
        reset_trigger_times()
        enable_event_callbacks()
        set_nvr_alarm_state("arm")
        logging.info(f"{lime_green_start}System armed immediately at startup.{reset}")

# Function to check the initial state at startup
def check_initial_state():
    if arm_disarm_button.is_pressed:
        logging.info(f"{red_bg_bold_white_text}Initial state check: ARMED{reset}")
        arm_system_immediately()
    else:
        logging.info(f"{green_bg_bold_white_text}Initial state check: DISARMED{reset}")
        disarm_system()

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

# Disarm Function
def disarm_system():
    global armed, countdown_in_progress
    if armed or countdown_in_progress:
        logging.info(f"{amber_start}Disarming system...{reset}")
        countdown_in_progress = False
        armed = False
        reset_trigger_times()
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

arm_disarm_button.when_pressed = arm_system
arm_disarm_button.when_released = disarm_system

def change_camera_alarm_state(camera_ip, sensor_state, user, password, camera_name):
    relay_channel = 0
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

def send_alarm_to_camera(camera_ip, camera_name):
    if TEST_MODE:
        logging.info(f"{lime_green_start}Test Mode ON - Alarm not sent to {camera_name} at {camera_ip}{reset}")
    else:
        change_camera_alarm_state(camera_ip, "NO", USER, PASSWORD, camera_name)
        time.sleep(2)
        change_camera_alarm_state(camera_ip, "NC", USER, PASSWORD, camera_name)

def on_detector_triggered(detector_id):
    global countdown_in_progress
    if countdown_in_progress:
        return

    detector_id_str = str(detector_id)
    detector_name = DETECTORS[detector_id_str]["name"]
    logging.info(f"{yellow_bg_black_text}Detector {detector_name} triggered{reset}")
    DETECTORS[detector_id_str]["last_triggered"] = datetime.now()
    logging.info(f"{pink_bg_black_text}Detector {detector_id_str} last triggered time set to {DETECTORS[detector_id_str]['last_triggered']}{reset}")
    check_for_confirmed_intrusion()

def on_camera_triggered(camera_id):
    global countdown_in_progress
    if countdown_in_progress:
        return

    camera_ip = IPCCTV[camera_id]["ip"]
    logging.info(f"{cyan_bg_black_text}{camera_id} - {camera_ip} triggered{reset}")
    IPCCTV[camera_id]["last_triggered"] = datetime.now()
    logging.info(f"{pink_bg_black_text}Camera {camera_id} last triggered time set to {IPCCTV[camera_id]['last_triggered']}{reset}")
    check_for_confirmed_intrusion()

def check_for_confirmed_intrusion():
    current_time = datetime.now()
    recent_cameras = {camera_id: camera for camera_id, camera in IPCCTV.items() if camera["last_triggered"] and (current_time - camera["last_triggered"]) <= TIME_THRESHOLD}
    recent_detectors = {detector_id: detector for detector_id, detector in DETECTORS.items() if detector["last_triggered"] and (current_time - detector["last_triggered"]) <= TIME_THRESHOLD}

    for camera_id, camera in recent_cameras.items():
        logging.info(f"{pink_bg_black_text}Checking camera {camera_id} with last triggered time {camera['last_triggered']}{reset}")
        for detector_id in camera["detectors"]:
            detector = recent_detectors.get(str(detector_id))
            if detector:
                logging.info(f"{pink_bg_black_text}Checking detector {detector_id} with last triggered time {detector['last_triggered']}{reset}")
                time_difference = abs(camera["last_triggered"] - detector["last_triggered"])
                logging.info(f"{pink_text}Time difference for {camera_id} and detector {detector_id}: {time_difference}{reset}")

                if time_difference <= TIME_THRESHOLD:
                    logging.info(f"{red_bg_bold_white_text}Confirmed intrusion detected by {camera_id} and detector {detector_id}{reset}")
                    send_alarm_to_camera(camera["ip"], camera_id)
                    camera["last_triggered"] = None
                    detector["last_triggered"] = None
                    break

def initialize_gpio():
    for camera_name, camera_info in IPCCTV.items():
        camera_info["device"] = gpiozero.Button(camera_info["pin"], pull_up=True, bounce_time=0.2)
        camera_info["device"].when_pressed = lambda name=camera_name: on_camera_triggered(name)

    for detector_id, detector_info in DETECTORS.items():
        detector_info["device"] = gpiozero.Button(detector_info["pin"], pull_up=True, bounce_time=0.2)
        detector_info["device"].when_pressed = lambda id=detector_id: on_detector_triggered(id)

initialize_gpio()
check_initial_state()

try:
    logging.info(
        f"{cyan_start}{'Test mode is active.' if TEST_MODE else 'Running in normal mode. Use --test-mode to activate test mode.'}\n\n" f"{reset}"
        f"{yellow_start}\n"
        "   _____                      ____           \n"
        "  / ___/___  ____  ________  / __ \\_________ \n"
        "  \\__ \\/ _ \\/ __ \\/ ___/ _ \\/ /_/ / ___/ __ \\\n"
        " ___/ /  __/ / / (__  )  __/ ____/ /  / /_/ /\n"
        "/____/\\___/_/ /_/____/\\___/_/   /_/   \\____/ \n"
        "                                             V1\n"
        f"{reset}\n"
        "SensePro is now running. Press CTRL+C to exit.\n\n"
    )

    while True:
        time.sleep(0.1)

except KeyboardInterrupt:
    logging.info(
        f"{yellow_start}\n"
        "   _____                      ____           \n"
        "  / ___/___  ____  ________  / __ \\_________ \n"
        "  \\__ \\/ _ \\/ __ \\/ ___/ _ \\/ /_/ / ___/ __ \\\n"
        " ___/ /  __/ / / (__  )  __/ ____/ /  / /_/ /\n"
        "/____/\\___/_/ /_/____/\\___/_/   /_/   \\____/ \n"
        "                                             V1      \n\n"
        "SensePro has now aborted.\n\n"
        f"{reset}"
    )
