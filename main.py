import json
import logging
import os
import pika
import sys
import uuid
from gpiozero import Button
from systemd.journal import JournalHandler

# Journal handler for system journal
handler = JournalHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logger = logging.getLogger('SenseProController')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

CONTROLLER_ID = os.getenv("CONTROLLER_ID")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")

# Check if the variable is set
if not CONTROLLER_ID:
    logger.error("Error: The CONTROLLER_ID environment variable is not set.")
    sys.exit(1)  # Exit with a non-zero status code to indicate an error

# Check if the variable is set
if not RABBITMQ_HOST:
    logger.error("Error: The RABBITMQ_HOST environment variable is not set.")
    sys.exit(1)  # Exit with a non-zero status code to indicate an error

# Check if the variable is set
if not RABBITMQ_USER:
    logger.error("Error: The RABBITMQ_USER environment variable is not set.")
    sys.exit(1)  # Exit with a non-zero status code to indicate an error

# Check if the variable is set
if not RABBITMQ_PASSWORD:
    logger.error("Error: The RABBITMQ_PASSWORD environment variable is not set.")
    sys.exit(1)  # Exit with a non-zero status code to indicate an error

logger.info(f"CONTROLLER_ID: {CONTROLLER_ID}")

CONFIG_FILE = "config.json"

# Function to get MAC address
def get_mac_address():
    mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 8 * 6, 8)][::-1])
    logger.info(f"Retrieved MAC address: {mac_address}")
    return mac_address

# Function to get serial number
def get_serial_number():
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line.startswith("Serial"):
                serial_number = line.strip().split(":")[1].strip()
                logger.info(f"Retrieved Serial Number: {serial_number}")
                return serial_number

# Function to load configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        logger.info(f"Loading configuration from {CONFIG_FILE}")
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    logger.warning(f"{CONFIG_FILE} not found. Proceeding without initial configuration.")
    return None

# Function to save configuration
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    logger.info(f"Configuration saved to {CONFIG_FILE}")

# Dictionary to store Button instances for pins
led_pins = {}

# Function to set up GPIO pins
def setup_gpio_pins(devices):
    global led_pins
    for device in devices:
        if "pin" in device and device["pin"] is not None:
            pin = device["pin"]
            if pin not in led_pins:
                led_pins[pin] = Button(pin, pull_up=True)
                logger.info(f"Set up pin {pin} as Button")
            led_pins[pin].close()  # Ensure it's off initially

# Function to process RabbitMQ message
def process_message(channel, method, properties, body):
    logger.info("Received new configuration message")
    new_config = json.loads(body)
    save_config(new_config)
    devices = new_config.get("devices", [])
    setup_gpio_pins(devices)
    logger.info(f"Set up {len(devices)} devices based on new configuration")

def main():
    serial_number = get_serial_number()
    logger.info(f"Starting controller with Serial Number: {serial_number}")

    # Load existing config or proceed without stopping
    config = load_config()
    if config:
        devices = config.get("devices", [])
        setup_gpio_pins(devices)
    else:
        logger.info("Waiting for configuration via RabbitMQ...")

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    queue_name = f"controller-{serial_number}"
    channel.queue_declare(queue=queue_name)
    logger.info(f"Listening for messages on queue: {queue_name}")

    try:
        channel.basic_consume(queue=queue_name, on_message_callback=process_message, auto_ack=True)
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Stopping controller...")
    except Exception as e:
        logger.error(f"Error during message consumption: {e}")
    finally:
        for led in led_pins.values():
            led.close()  # Release GPIO pins
        connection.close()
        logger.info("RabbitMQ connection closed")

if __name__ == "__main__":
    main()
