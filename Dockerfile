# Use an official Python runtime as the base image
FROM python:3.13-slim

ARG CONTROLLER_ID
ENV CONTROLLER_ID=${CONTROLLER_ID}
ARG RABBITMQ_HOST
ENV RABBITMQ_HOST=${RABBITMQ_HOST}
ARG RABBITMQ_USER
ENV RABBITMQ_USER=${RABBITMQ_USER}
ARG RABBITMQ_PASSWORD
ENV RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Define the command to run the application
CMD ["python", "main.py"]
