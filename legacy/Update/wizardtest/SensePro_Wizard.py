#!/usr/bin/env python3
import sys
import json
import re
import getpass
import os
import ipaddress

# Define color codes for logging
red_start = "\033[91m"  # ANSI code for Red text
amber_start = "\033[33m"  # ANSI code for Amber text
lime_green_start = "\033[92m"  # ANSI code for Lime Green text
cyan_start = "\033[36m"  # ANSI code for Cyan text
reset = "\033[0m"  # ANSI reset code

# ASCII Art definition
SensePro_art = f"{lime_green_start}\n\n"\
    "   _____                      ____           \n"\
    "  / ___/___  ____  ________  / __ \\_________ \n"\
    "  \\__ \\/ _ \\/ __ \\/ ___/ _ \\/ /_/ / ___/ __ \\\n"\
    " ___/ /  __/ / / (__  )  __/ ____/ /  / /_/ /\n"\
    "/____/\\___/_/ /_/____/\\___/_/   /_/   \\____/ \n"\
    "                                             V1      \n\n"\
    "SensePro Wizard.\n\n"\
    f"{reset}"

# GPIO mapping for physical alarm inputs
pai_to_gpio_map = {
    1: 4,  2: 5,  3: 6,  4: 7,
    5: 8,  6: 9,  7: 10, 8: 11,
    9: 12, 10: 13, 11: 16, 12: 17,
    13: 18, 14: 19, 15: 20, 16: 21
}

# Handle keyboard interrupt
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

# Create env file
def create_env_file(nvr_user, nvr_password):
    env_file_path = './SensePro_env.env'  # Create the file in the current directory
    try:
        with open(env_file_path, 'w') as env_file:
            env_file.write(f'NVR_USERNAME={nvr_user}\n')
            env_file.write(f'NVR_PASSWORD={nvr_password}\n')
        print(f"Environment file created successfully at {env_file_path}")
    except IOError as e:
        print(f"Failed to create environment file: {e}")

# Validate IP address
def is_valid_ip(ip_addr):
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    ip_parts = ip_addr.split(':')
    if not re.match(ipv4_pattern, ip_parts[0]):
        return False
    try:
        ip = ipaddress.ip_address(ip_parts[0])
        if type(ip) is not ipaddress.IPv4Address:
            return False
    except ValueError:
        return False
    if len(ip_parts) > 1:
        try:
            port = int(ip_parts[1])
            if port < 0 or port > 65535:
                return False
        except ValueError:
            return False
    return True

# Prompt for the number of physical alarm inputs
def prompt_for_alarm_inputs():
    while True:
        response = input(f"{amber_start}\nHow many Physical Alarm Inputs are required (Specify either a single input for example PAI1 or a range PAI1-16 for all)? {reset}")
        try:
            if '-' in response:
                start, end = map(int, re.sub('[^0-9-]', '', response).split('-'))
                return list(range(start, end + 1))
            else:
                return [int(re.sub('[^0-9]', '', response))]
        except ValueError:
            print(f"{red_start}Invalid input. Please enter a valid number or range.{reset}")

# Prompt for input type selection
def prompt_for_input_type(pai_number, arm_disarm_used):
    while True:
        options = f"{cyan_start}\n1. IPC\n2. Detector\n"
        if not arm_disarm_used:
            options += "3. Arm/Disarm Trigger\n"
        response = input(f"{amber_start}\nFor PAI{pai_number}, specify whether you are using an IP CCTV camera or Detector.{reset}{options}Please make a selection: {reset}")
        if response in ['1', '2'] or (response == '3' and not arm_disarm_used):
            return int(response)
        else:
            print(f"{red_start}Invalid selection. Please choose a valid option.{reset}")

# Prompt for protocol selection
def prompt_for_protocol():
    while True:
        response = input(f"{amber_start}\nSpecify the protocol (http or https): {reset}")
        if response.lower() in ['http', 'https']:
            return response.lower()
        else:
            print(f"{red_start}Invalid protocol. Please enter 'http' or 'https'.{reset}")

# Prompt for defining rules
def prompt_for_rules(config):
    rules = []
    while True:
        rule = {}
        rule_name = input(f"{amber_start}\nEnter a name for this rule: {reset}")
        rule['name'] = rule_name

        # Get IPCCTV selection for the rule
        ipcctv_list = "\n".join([f"{i + 1}. {ipc['name']} - (IP {ipc['ip']})" for i, ipc in enumerate(config['ipcctv'].values())])
        ipcctv_selection = input(f"{amber_start}\nSelect IPCCTV(s) for this rule.\n{cyan_start}{ipcctv_list}\n\nPlease make a selection (e.g., 1, 1,4,6, or a range 1-4 or 'omit' to skip): {reset}")
        ipcctvs = []
        if ipcctv_selection.lower() != 'omit':
            try:
                if '-' in ipcctv_selection:
                    start, end = map(int, re.sub('[^0-9-]', '', ipcctv_selection).split('-'))
                    ipcctvs = list(range(start, end + 1))
                else:
                    ipcctvs = [int(d.strip()) for d in ipcctv_selection.split(',')]
            except ValueError:
                print(f"{red_start}Invalid input. Please enter a valid number or range.{reset}")
        rule['ipcctvs'] = [list(config['ipcctv'].keys())[i - 1] for i in ipcctvs]

        # Get detector selection for the rule
        detector_list = "\n".join([f"{i + 1}. {det['name']} - (PAI {pai})" for i, (pai, det) in enumerate(config['detectors'].items())])
        detector_selection = input(f"{amber_start}\nSelect detector(s) for this rule.\n{cyan_start}{detector_list}\n\nPlease make a selection (e.g., 1, 1,4,6, or a range 1-4 or 'omit' to skip): {reset}")
        detectors = []
        if detector_selection.lower() != 'omit':
            try:
                if '-' in detector_selection:
                    start, end = map(int, re.sub('[^0-9-]', '', detector_selection).split('-'))
                    detectors = list(range(start, end + 1))
                else:
                    detectors = [int(d.strip()) for d in detector_selection.split(',')]
            except ValueError:
                print(f"{red_start}Invalid input. Please enter a valid number or range.{reset}")
        rule['detectors'] = detectors

        rule_type = input(f"{amber_start}\nEnter the rule type (all, any): {reset}")
        rule['type'] = rule_type

        rules.append(rule)

        more_rules = input(f"{amber_start}\nWould you like to add another rule? (yes/no): {reset}")
        if more_rules.lower() != 'yes':
            break

    return rules

# Main configuration function
def create_config():
    try:
        # Get NVR name
        nvr_name = input(f"{amber_start}\nPlease provide a name for this NVR: {reset}")

        # Get NVR/IPC details
        while True:
            nvr_ip = input(f"{amber_start}\nEnter the IP/Hostname[:port] of the NVR/IPC: {reset}")
            if is_valid_ip(nvr_ip):
                break
            else:
                print(f"{red_start}Invalid IP address format or range. Please enter a valid IP address.{reset}")

        nvr_protocol = prompt_for_protocol()
        nvr_user = input(f"{amber_start}\nEnter the NVR/IPC username for authentication: {reset}")
        nvr_password = getpass.getpass(f"{amber_start}\nEnter the NVR/IPC password for authentication: {reset}")

        # Create env file
        create_env_file(nvr_user, nvr_password)

        # Get number of physical alarm inputs
        alarm_inputs = prompt_for_alarm_inputs()

        # Initialize configuration data
        config = {
            "system_settings": {},
            "NVRs": {},
            "ipcctv": {},
            "detectors": {},
            "time_threshold": 0,
            "rules": []
        }

        arm_disarm_used = False
        used_ips = set()
        used_names = set()

        for alarm_input in alarm_inputs:
            input_type = prompt_for_input_type(alarm_input, arm_disarm_used)

            if input_type == 1:
                # IPC setup
                while True:
                    ip = input(f"{amber_start}\nEnter the IP/Hostname[:port] for IPC at Physical Alarm Input {alarm_input}: {reset}")
                    if not is_valid_ip(ip):
                        print(f"{red_start}Invalid IP address format or range. Please enter a valid IP address.{reset}")
                        continue
                    if ip in used_ips:
                        print(f"{red_start}IP address {ip} is already in use. Please enter a unique IP address.{reset}")
                        continue
                    used_ips.add(ip)
                    break

                protocol = prompt_for_protocol()

                while True:
                    name = input(f"{amber_start}\nSpecify a Name for this IPC: {reset}")
                    if name in used_names:
                        print(f"{red_start}Name {name} is already in use. Please enter a unique name.{reset}")
                        continue
                    used_names.add(name)
                    break

                config["ipcctv"][f"IPC {alarm_input} - {name}"] = {
                    "protocol": protocol,
                    "ip": ip,
                    "pin": pai_to_gpio_map[alarm_input],
                    "name": name,
                    "detectors": []
                }
            elif input_type == 2:
                # Detector setup
                while True:
                    name = input(f"{amber_start}\nPlease name the detector at PAI{alarm_input}: {reset}")
                    if name in used_names:
                        print(f"{red_start}Name {name} is already in use. Please enter a unique name.{reset}")
                        continue
                    used_names.add(name)
                    break

                config["detectors"][alarm_input] = {
                    "pin": pai_to_gpio_map[alarm_input],
                    "name": name
                }
            elif input_type == 3:
                # Arm/Disarm trigger setup
                if arm_disarm_used:
                    print(f"{red_start}Arm/Disarm Trigger already configured. Please choose another option.{reset}")
                    continue
                else:
                    arm_disarm_used = True
                    state = input(f"{amber_start}\nPAI{alarm_input} has been designated as an Arm/Disarm. What state will be armed (NO or NC): {reset}")
                    duration = int(input(f"{amber_start}\nSpecify a countdown duration for when being armed (in seconds): {reset}"))
                    config["system_settings"]["arm_disarm_pin"] = pai_to_gpio_map[alarm_input]
                    config["system_settings"]["countdown_duration"] = duration
                    config["NVRs"][nvr_name] = {
                        "protocol": nvr_protocol,
                        "ip": nvr_ip,
                        "arm": {
                            "input": f"Alarm[{alarm_input}].SensorType",
                            "relay": state.upper()
                        },
                        "disarm": {
                            "input": f"Alarm[{alarm_input}].SensorType",
                            "relay": "NC" if state.upper() == "NO" else "NO"
                        }
                    }

        # Map detectors to IPCs
        for ipc_name, ipc_info in config["ipcctv"].items():
            detector_list = "\n".join([f"{i + 1}. {det['name']} - (PAI{d})" for i, (d, det) in enumerate(config["detectors"].items())])
            while True:
                detector_selection = input(f"{amber_start}\nMap detector/s for {ipc_info['name']} at PAI{ipc_info['pin']}.\n{cyan_start}Detector list\n{detector_list}\n{len(config['detectors']) + 1}. Omit\n\nPlease make a selection for example (1, 1,4,6, or a range 1-4 or Omit): {reset}")
                if detector_selection.lower() == 'omit':
                    break
                try:
                    detectors = []
                    if '-' in detector_selection:
                        start, end = map(int, re.sub('[^0-9-]', '', detector_selection).split('-'))
                        detectors = list(range(start, end + 1))
                    else:
                        detectors = [int(d.strip()) for d in detector_selection.split(',')]
                    for d in detectors:
                        config["ipcctv"][ipc_name]["detectors"].append(d)
                    break
                except ValueError:
                    print(f"{red_start}Invalid input. Please enter a valid number or range.{reset}")

        # Time threshold
        config["time_threshold"] = int(input(f"{amber_start}\nEnter time threshold in minutes for confirming intrusion: {reset}"))

        # Prompt for rules
        config["rules"] = prompt_for_rules(config)

        # Write to JSON file
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)

        # Log GPIO mappings
        try:
            with open('gpio_mappings.txt', 'w') as gpio_file:
                arm_disarm_pin = config["system_settings"].get("arm_disarm_pin")
                for alarm_input in alarm_inputs:
                    mapping_info = f"Physical Alarm Input {alarm_input} - Mapped to - "
                    if arm_disarm_pin and pai_to_gpio_map[alarm_input] == arm_disarm_pin:
                        state = config["NVRs"][nvr_name]["arm"]["relay"]
                        mapping_info += f"Arm/Disarm (State set to {state} for ARM)\n"
                    elif any(ipc_info["pin"] == pai_to_gpio_map[alarm_input] for ipc_info in config["ipcctv"].values()):
                        ipc_name = next(key for key, ipc_info in config["ipcctv"].items() if ipc_info["pin"] == pai_to_gpio_map[alarm_input])
                        ipc = config["ipcctv"][ipc_name]
                        mapping_info += f"IPC {ipc['name']} at IP {ipc['ip']}\n"
                    elif alarm_input in config["detectors"]:
                        detector = config["detectors"][alarm_input]
                        mapping_info += f"Detector {detector['name']}\n"
                    else:
                        mapping_info += "No mapping found\n"
                    gpio_file.write(mapping_info)
        except IOError as e:
            print(f"{red_start}Failed to write GPIO mappings file: {e}{reset}")

        print("\033[92mConfiguration file created successfully.\033[0m")

    except KeyboardInterrupt:
        handle_keyboard_interrupt()
        sys.exit(1)

    except Exception as e:
        print(f"{red_start}An error occurred: {e}{reset}")
        sys.exit(1)

def main():
    print(SensePro_art)
    create_config()
    print(f"{lime_green_start}\nConfiguration process completed. Exiting the application.\n{reset}")
    sys.exit(0)

if __name__ == "__main__":
    main()
