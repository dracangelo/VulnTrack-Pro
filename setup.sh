#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize DB
flask db upgrade

echo "Setup complete! Run ./start.sh to start the server."
