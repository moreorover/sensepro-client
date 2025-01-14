#!/bin/bash
# start_SensePro.sh - Script to start SensePro.py on boot
screen -dmS SensePro_session bash -c 'cd /home/admin/SensePro; python3 SensePro.py'
