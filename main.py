import os
import json
import uuid
import pika
import logging
from gpiozero import Button

CONFIG_FILE = "config.json"

# Configure logging
# logging.basicConfig(
#     filename="controller.log",
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s"
# )

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("controller.log"),
        logging.StreamHandler()  # This adds console output
    ]
)

# Function to get MAC address
def get_mac_address():
    mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 8 * 6, 8)][::-1])
    logging.info(f"Retrieved MAC address: {mac_address}")
    return mac_address

# Function to get serial number
def get_serial_number():
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("Serial"):
                    serial_number = line.strip().split(":")[1].strip()
                    logging.info(f"Retrieved Serial Number: {serial_number}")
                    return serial_number
    except Exception as e:
        logging.error(f"Failed to retrieve serial number: {e}")
        return "0000000000000000"

# Function to load configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        logging.info(f"Loading configuration from {CONFIG_FILE}")
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    logging.warning(f"{CONFIG_FILE} not found. Proceeding without initial configuration.")
    return None

# Function to save configuration
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    logging.info(f"Configuration saved to {CONFIG_FILE}")

# Dictionary to store Button instances for pins
led_pins = {}

# Function to set up GPIO pins
def setup_gpio_pins(devices):
    global led_pins
    for device in devices:
        if "pin" in device and device["pin"] is not None:
            pin = device["pin"]
            if pin not in led_pins:
                # led_pins[pin] = Button(pin, pull_up=True)
                logging.info(f"Set up pin {pin} as Button")
            # led_pins[pin].close()  # Ensure it's off initially

# Function to process RabbitMQ message
def process_message(channel, method, properties, body):
    logging.info("Received new configuration message")
    new_config = json.loads(body)
    save_config(new_config)
    devices = new_config.get("devices", [])
    setup_gpio_pins(devices)
    logging.info(f"Set up {len(devices)} devices based on new configuration")

def main():
    mac_address = get_mac_address()
    serial_number = get_serial_number()
    logging.info(f"Starting controller with MAC Address: {mac_address}, Serial Number: {serial_number}")

    # Load existing config or proceed without stopping
    config = load_config()
    if config:
        devices = config.get("devices", [])
        setup_gpio_pins(devices)
    else:
        logging.info("Waiting for configuration via RabbitMQ...")

    # RabbitMQ connection settings
    rabbitmq_host = "localhost"
    rabbitmq_username = "user"
    rabbitmq_password = "password"

    credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
    connection_params = pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    queue_name = f"controller-{serial_number}"
    channel.queue_declare(queue=queue_name)
    logging.info(f"Listening for messages on queue: {queue_name}")

    try:
        channel.basic_consume(queue=queue_name, on_message_callback=process_message, auto_ack=True)
        channel.start_consuming()
    except KeyboardInterrupt:
        logging.info("Stopping controller...")
    except Exception as e:
        logging.error(f"Error during message consumption: {e}")
    finally:
        for led in led_pins.values():
            led.close()  # Release GPIO pins
        connection.close()
        logging.info("RabbitMQ connection closed")

if __name__ == "__main__":
    main()
