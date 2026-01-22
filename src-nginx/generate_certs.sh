#!/bin/bash

# Use the first argument as the directory, or default to "./certs" if empty
certs_dir="${1:-./certs}"

mkdir -p "$certs_dir"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$certs_dir/nginx.key" \
    -out "$certs_dir/nginx.crt" \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

echo "Certificates generated in $certs_dir/"
