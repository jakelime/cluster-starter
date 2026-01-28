#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration with Defaults
# ---------------------------
# Syntax: ${VAR:-default_value}
static_folder="${NGINX_STATIC_FOLDER:-/datashare/www/static}"
media_folder="${NGINX_MEDIA_FOLDER:-/datashare/www/media}"
nginx_user="${NGINX_USER:-nginx:nginx}"

echo "Starting nginx data directory initialization..."
echo "Static folder: $static_folder"
echo "Media folder:  $media_folder"
echo "User:          $nginx_user"

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
ensure_dir "$static_folder"
ensure_dir "$media_folder"

echo "nginx data dir init done."
