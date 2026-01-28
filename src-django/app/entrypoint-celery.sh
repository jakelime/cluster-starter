#!/bin/bash

# Best Practice: Wait for Valkey/Redis to be available before starting Celery
# This uses the 'wait-for-it.sh' script or similar, often included in base images.
# If you don't use a wait script, a simple sleep will suffice for development.
# echo "Waiting for message broker (Valkey) to be ready..."
# /usr/local/bin/wait-for-it.sh valkey:6379 --timeout=30 -- echo "Valkey is up!"

# Execute the Celery worker command
echo "Starting Celery worker..."
# The "$@" ensures any arguments passed in docker-compose (e.g., -c 4) are used
exec celery -A main worker -l info "$@"