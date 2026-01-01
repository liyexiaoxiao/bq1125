#!/bin/bash
set -e

# Run database migrations
flask db upgrade

# Start the application
exec python start.py
