#!/bin/bash

# Set variables
COMPOSE_FILE="docker-compose.yaml"
DEPLOY_DIR="/opt/sensepro-controller"

# Ensure the script stops on any error
set -e

# Load environment variables passed by GitHub Actions
export RABBITMQ_USER=${RABBITMQ_USER}
export RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}
export RASPBERRY_PI_SERIAL=$(cat /proc/cpuinfo | grep Serial | awk '{print $3}')

# Create the deployment directory if it doesn't exist
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "Creating deployment directory: $DEPLOY_DIR"
    sudo mkdir -p "$DEPLOY_DIR"
fi

# Move to the deployment directory
cd "$DEPLOY_DIR"

# Copy the docker compose file to the deployment directory
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Docker compose file not found!"
    exit 1
fi

# Stop existing services (if any)
echo "Stopping existing services..."
sudo docker compose -f "$COMPOSE_FILE" down

# Pull the latest image
echo "Pulling the latest image..."
sudo docker compose -f "$COMPOSE_FILE" pull

# Start the services
echo "Starting services..."
sudo docker compose -f "$COMPOSE_FILE" up -d

# Clean up unused Docker resources
echo "Cleaning up unused Docker resources..."
sudo docker system prune -f

# Verify services are running
echo "Verifying services..."
sudo docker compose -f "$COMPOSE_FILE" ps

echo "Deployment completed successfully!"
