ARG url_docker=docker.io
ARG port_valkey=6379
FROM ${url_docker}/valkey/valkey:8.1.4-alpine

ARG port_valkey
ENV VALKEY_PORT=${port_valkey}

COPY init.sh /usr/local/bin/init.sh
RUN chmod +x /usr/local/bin/init.sh
ENTRYPOINT ["/usr/local/bin/init.sh"]