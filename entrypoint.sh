#!/bin/bash
set -e

# Run database migrations
flask db upgrade

# Initialize database and seed admin
python seed_admin.py

# Start the application
exec python start.py
