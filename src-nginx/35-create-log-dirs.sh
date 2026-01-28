#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration with Defaults
# ---------------------------
# Syntax: ${VAR:-default_value}
NGINX_LOG_FOLDER="${NGINX_LOG_FOLDER:-/applogs/nginx}"
nginx_user="${NGINX_USER:-nginx:nginx}"

echo "Starting nginx logs directory initialization..."
echo "Applogs folder: $NGINX_LOG_FOLDER"

# Function to ensure directory exists and has correct ownership
ensure_dir() {
    local dir_path="$1"

    if [ ! -d "$dir_path" ]; then
        echo "Creating directory: $dir_path"
        mkdir -p "$dir_path"
    fi

    echo "Setting ownership for: $dir_path"
    chown -R "$nginx_user" "$dir_path"
}

# Run setup
ensure_dir "$NGINX_LOG_FOLDER"

echo "nginx logs dir init done."
