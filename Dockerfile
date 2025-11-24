# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (Nmap, OpenVAS dependencies if needed)
# OpenVAS is complex to containerize fully in one go, so we'll focus on Nmap and the App
RUN apt-get update && apt-get install -y \
    nmap \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose port 5000
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the application
CMD ["./start.sh"]
