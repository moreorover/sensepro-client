import json
import os
import pika

SEND_CONFIG_FILE = "send_config.json"

def load_send_config():
    if not os.path.exists(SEND_CONFIG_FILE):
        print(f"{SEND_CONFIG_FILE} not found!")
        return None

    with open(SEND_CONFIG_FILE, "r") as f:
        return json.load(f)

def send_message_to_queue():
    # Load configuration to send
    config = load_send_config()
    if config is None:
        return

    # RabbitMQ connection settings
    rabbitmq_host = "localhost"
    rabbitmq_username = "user"
    rabbitmq_password = "password"
    queue_name = "controller-0000000000000000"

    # RabbitMQ connection
    credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
    connection_params = pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    # Declare queue
    channel.queue_declare(queue=queue_name)

    # Convert config to JSON string and send as message
    message = json.dumps(config)
    channel.basic_publish(exchange='', routing_key=queue_name, body=message)

    print(f"Configuration sent to queue {queue_name}")

    connection.close()

if __name__ == "__main__":
    send_message_to_queue()
