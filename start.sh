#!/bin/bash
# Apply migrations
flask db upgrade

# Start server
# Using gunicorn for production would be better, but flask run is fine for now as per Dockerfile
# Or better:
exec gunicorn -w 4 -b 0.0.0.0:5500 run:app
