#!/bin/bash

# Define variables
REMOTE_HOST="raspberrypi"
REMOTE_USER="pi"
REMOTE_DIR="/home/pi/dev/sensepro-client"

# Clear the remote directory before uploading
ssh ${REMOTE_USER}@${REMOTE_HOST} "find ${REMOTE_DIR} -mindepth 1 ! -name 'venv' -exec rm -rf {} +"

# Generate an rsync exclude file from .gitignore
# Filter all ignored files, including untracked ones
git ls-files --others --ignored --exclude-standard > .rsync-ignore

# Add the legacy folder to the exclude file
echo "legacy/" >> .rsync-ignore
echo ".git/" >> .rsync-ignore
echo ".idea/" >> .rsync-ignore

# Ensure patterns from .gitignore take effect
if [ -f ".gitignore" ]; then
  cat .gitignore >> .rsync-ignore
fi

# Remove the .env.local entry from .rsync-ignore
sed -i '/\.env\.local/d' .rsync-ignore

# Run rsync to upload files, excluding .rsync-ignore patterns
rsync -av --exclude-from='.rsync-ignore' ./ "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"

# Clean up the .rsync-ignore file
rm .rsync-ignore

# Notify the user
echo "Files uploaded to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}, excluding .gitignore patterns and the legacy folder."
