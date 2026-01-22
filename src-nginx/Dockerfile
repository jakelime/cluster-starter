ARG url_docker=docker.io
FROM ${url_docker}/nginx:1.29.3-trixie

# Copy the Nginx configuration file
COPY ./nginx.conf /etc/nginx/nginx.conf

# Copy the Nginx template files
COPY ./templates /etc/nginx/templates

# Copy the SSL certificates
COPY ./certs /etc/nginx/certs

# Copy the custom-error html files
COPY ./custom-errors /usr/share/nginx/html/


# Add startup scripts
COPY ./35-create-log-dirs.sh /docker-entrypoint.d/35-create-log-dirs.sh
RUN chmod +x /docker-entrypoint.d/35-create-log-dirs.sh
COPY ./36-create-datashare-static-media.sh /docker-entrypoint.d/36-create-datashare-static-media.sh
RUN chmod +x /docker-entrypoint.d/36-create-datashare-static-media.sh