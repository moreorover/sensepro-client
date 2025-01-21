#!/bin/bash

# Variables
SERVICE_NAME="sensepro-controller.service"
INSTALL_DIR="/opt/sensepro-controller"
SERVICE_DIR="/etc/systemd/system"

serial=$(grep Serial /proc/cpuinfo | awk '{print $3}')

echo "[INFO] Device Serial Number: ${serial}"

# RabbitMQ-related environment variables
mq_host="sensepro-server-dev"
mq_user=""
mq_password=""

echo "[INFO] Ensuring python3-rpi.gpio is installed..."
#sudo apt-get install python3-rpi.gpio
sudo apt-get install -y python3-gpiozero python3-pika python3-systemd

# Step 5: Create or update the service file
echo "[INFO] Creating/updating systemd service file..."
cat <<EOF | sudo tee "$SERVICE_DIR/$SERVICE_NAME"
[Unit]
Description=SensePro Controller Service
After=network.target

[Service]
ExecStart=/usr/bin/python ${INSTALL_DIR}/main.py
Restart=always
Environment="RABBITMQ_HOST=${mq_host}"
Environment="RABBITMQ_USER=${mq_user}"
Environment="RABBITMQ_PASSWORD=${mq_password}"
WorkingDirectory=$INSTALL_DIR
User=pi
Group=pi
StandardOutput=journal
StandardError=journal
SyslogIdentifier=SenseProController

[Install]
WantedBy=multi-user.target
EOF

# Step 6: Reload systemd and restart the service
echo "[INFO] Reloading systemd and restarting the service..."
sudo systemctl daemon-reload
sudo systemctl restart "$SERVICE_NAME"

# Step 7: Enable the service on boot
echo "[INFO] Enabling the service to start on boot..."
sudo systemctl enable "$SERVICE_NAME"

# Step 8: Display service status
echo "[INFO] Deployment complete. Service status:"
sudo systemctl status "$SERVICE_NAME"
