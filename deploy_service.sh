#!/bin/bash

# Variables
SCRIPT_NAME="main.py"
BINARY_NAME="sensepro-controller"
SERVICE_NAME="sensepro-controller.service"
INSTALL_DIR="/usr/local/bin"
SERVICE_DIR="/etc/systemd/system"
LOG_FILE="/var/log/sensepro-controller.log"

controller_id="00000000000"

# RabbitMQ-related environment variables
mq_host="sensepro-server-dev"
mq_user=""
mq_password=""

# Step 1: Ensure pyinstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "[INFO] Installing PyInstaller..."
    pip install pyinstaller || { echo "[ERROR] Failed to install PyInstaller."; exit 1; }
fi

# Step 2: Build the binary
echo "[INFO] Building binary with PyInstaller..."
pyinstaller --onefile "$SCRIPT_NAME" --name "$BINARY_NAME" || { echo "[ERROR] Failed to build binary."; exit 1; }

# Step 3: Move binary to the install directory
echo "[INFO] Moving binary to $INSTALL_DIR..."
sudo mv "dist/$BINARY_NAME" "$INSTALL_DIR" || { echo "[ERROR] Failed to move binary."; exit 1; }

# Step 4: Ensure the log file exists
echo "[INFO] Ensuring log file exists at $LOG_FILE..."
sudo touch "$LOG_FILE"
sudo chown pi:pi "$LOG_FILE"
sudo chmod 600 "$LOG_FILE"

# Step 5: Create or update the service file
echo "[INFO] Creating/updating systemd service file..."
cat <<EOF | sudo tee "$SERVICE_DIR/$SERVICE_NAME"
[Unit]
Description=SensePro Controller Service
After=network.target

[Service]
ExecStart=$INSTALL_DIR/$BINARY_NAME
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
