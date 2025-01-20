#!/bin/bash

# Variables
SERVICE_NAME="sensepro-controller.service"
INSTALL_DIR="/opt/sensepro-controller"
SERVICE_DIR="/etc/systemd/system"
LOG_FILE="/opt/sensepro-controller/logs/sensepro-controller.log"

controller_id="00000000000"

# RabbitMQ-related environment variables
mq_host="sensepro-server-dev"
mq_user=""
mq_password=""

# Step 4: Ensure the log file exists
echo "[INFO] Ensuring log file exists at $LOG_FILE..."
sudo mkdir -p "$INSTALL_DIR"/logs
sudo touch "$LOG_FILE"
sudo chown -R pi:pi "$INSTALL_DIR"
sudo chmod 600 "$LOG_FILE"

# Step 5: Create or update the service file
echo "[INFO] Creating/updating systemd service file..."
cat <<EOF | sudo tee "$SERVICE_DIR/$SERVICE_NAME"
[Unit]
Description=SensePro Controller Service
After=network.target

[Service]
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/main.py
Restart=always
Environment="CONTROLLER_ID=${controller_id}"
Environment="RABBITMQ_HOST=${mq_host}"
Environment="RABBITMQ_USER=${mq_user}"
Environment="RABBITMQ_PASSWORD=${mq_password}"
Environment="LOG_FILE=${LOG_FILE}"
WorkingDirectory=$INSTALL_DIR
User=pi
Group=pi
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=sensepro_controller_service

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
