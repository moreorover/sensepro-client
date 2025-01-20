#!/bin/bash

# Define variables
REMOTE_HOST="raspberrypi"
REMOTE_USER="pi"
REMOTE_DIR="/opt/sensepro-controller"

ssh "${REMOTE_USER}@${REMOTE_HOST}" "sudo mkdir -p ${REMOTE_DIR}"

# Run rsync to upload files, excluding .rsync-ignore patterns
rsync --recursive --delete ./ "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"

ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${REMOTE_DIR} && python3 -m venv venv && source venv/bin/activate && pip install -r ${REMOTE_DIR}/requirements.txt"
