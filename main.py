import json
import logging
import os
import pika
import sys
import uuid
from gpiozero import Button
from logging.handlers import TimedRotatingFileHandler
from systemd.journal import JournalHandler

# Configure logging
LOG_FILE = os.getenv("LOG_FILE")
logger = logging.getLogger("sensepro_controller")
logger.setLevel(logging.INFO)

# Create a rotating file handler (rotates every 7 days)
handler = TimedRotatingFileHandler(LOG_FILE, when="midnight", interval=1, backupCount=7)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Journal handler for logging to system journal
try:
    journal_handler = JournalHandler()
    journal_formatter = logging.Formatter('%(message)s')
    journal_handler.setFormatter(journal_formatter)
    logger.addHandler(journal_handler)
except Exception as e:
    print(f"Error setting up journal logging: {e}", file=sys.stderr)

CONTROLLER_ID = os.getenv("CONTROLLER_ID")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")

# Check if the variable is set
if not LOG_FILE:
    logging.error("Error: The LOG_FILE environment variable is not set.")
    sys.exit(1)  # Exit with a non-zero status code to indicate an error

# Check if the variable is set
if not CONTROLLER_ID:
    logging.error("Error: The CONTROLLER_ID environment variable is not set.")
    sys.exit(1)  # Exit with a non-zero status code to indicate an error

# Check if the variable is set
if not RABBITMQ_HOST:
    logging.error("Error: The RABBITMQ_HOST environment variable is not set.")
    sys.exit(1)  # Exit with a non-zero status code to indicate an error

# Check if the variable is set
if not RABBITMQ_USER:
    logging.error("Error: The RABBITMQ_USER environment variable is not set.")
    sys.exit(1)  # Exit with a non-zero status code to indicate an error

# Check if the variable is set
if not RABBITMQ_PASSWORD:
    logging.error("Error: The RABBITMQ_PASSWORD environment variable is not set.")
    sys.exit(1)  # Exit with a non-zero status code to indicate an error

logging.info(f"CONTROLLER_ID: {CONTROLLER_ID}")

CONFIG_FILE = "config.json"

# Function to get MAC address
def get_mac_address():
    mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 8 * 6, 8)][::-1])
    logging.info(f"Retrieved MAC address: {mac_address}")
    return mac_address

# Function to get serial number
def get_serial_number():
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line.startswith("Serial"):
                serial_number = line.strip().split(":")[1].strip()
                logging.info(f"Retrieved Serial Number: {serial_number}")
                return serial_number

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
                led_pins[pin] = Button(pin, pull_up=True)
                logging.info(f"Set up pin {pin} as Button")
            led_pins[pin].close()  # Ensure it's off initially

# Function to process RabbitMQ message
def process_message(channel, method, properties, body):
    logging.info("Received new configuration message")
    new_config = json.loads(body)
    save_config(new_config)
    devices = new_config.get("devices", [])
    setup_gpio_pins(devices)
    logging.info(f"Set up {len(devices)} devices based on new configuration")

def main():
    serial_number = get_serial_number()
    logging.info(f"Starting controller with Serial Number: {serial_number}")

    # Load existing config or proceed without stopping
    config = load_config()
    if config:
        devices = config.get("devices", [])
        setup_gpio_pins(devices)
    else:
        logging.info("Waiting for configuration via RabbitMQ...")

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
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
