#!/bin/bash

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# Install python3-requests and python3-gpiozero
echo "Installing requests and gpiozero..."
sudo apt-get install -y python3-requests python3-gpiozero

# Install screen
echo "Installing screen..."
sudo apt-get install -y screen

# Set permissions for SensePro.py
echo "Setting permissions for SensePro.py..."
sudo chmod +x /home/admin/SensePro/SensePro.py
sudo chmod +x /home/admin/SensePro/SensePro_Wizard.py

# Create start_SensePro.sh
echo "Creating start_SensePro.sh..."
cat <<'EOF' > /home/admin/SensePro/start_SensePro.sh
#!/bin/bash
# start_SensePro.sh - Script to start SensePro.py on boot
screen -dmS SensePro_session bash -c 'cd /home/admin/SensePro; python3 SensePro.py'
EOF

# Set permissions for start_SensePro.sh
echo "Setting permissions for start_SensePro.sh..."
sudo chmod +x /home/admin/SensePro/start_SensePro.sh

# Add start_SensePro.sh to crontab for execution at boot
echo "Adding start_SensePro.sh to crontab..."
(crontab -l 2>/dev/null; echo "@reboot /bin/bash /home/admin/SensePro/start_SensePro.sh") | crontab -

# Schedule a daily reboot at 23:59 - do this as root sudo crontab -e
#echo "Scheduling daily reboot at 23:59..."
#(crontab -l 2>/dev/null; echo "0 0 * * * /sbin/shutdown -r now") | crontab -

echo "All necessary libraries are installed, permissions are set, Python scripts are created, and SensePro is scheduled to run at boot. A daily reboot at 23:59 is also scheduled."
