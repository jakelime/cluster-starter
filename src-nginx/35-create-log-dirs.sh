#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration with Defaults
# ---------------------------
# Syntax: ${VAR:-default_value}
LOGS_VOL="${SHARED_LOGS_DIR:-/applogs}"

applogs_dir="${LOGS_VOL}/nginx"
nginx_user="${NGINX_USER:-nginx:nginx}"

echo "Starting nginx logs directory initialization..."
echo "Applogs folder: $applogs_dir"

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
ensure_dir "$applogs_dir"

echo "nginx logs dir init done."
