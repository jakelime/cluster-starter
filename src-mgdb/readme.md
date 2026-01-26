# Docker builder for MongoDB

Builds a MongoDB docker instance.

This is designed to be a git submodule to be used as part of
the docker-compose orchestration.

## Quickstart

Use this as subrepo in a docker-compose
orchestration structure here: [Folder Structure](#Folder Structure).

## Folder Structure

```text
.[docker-compose root dir]
├── src-mgdb/ (this repo)
│   ├── .env
│   ├── .env.example
│   ├── Dockerfile
│   └── init-db.js
├── [ ... ]/ (other git submodule)
├── .env
├── .gitignore
├── .gitmodules
├── docker-compose.yml
└── readme.md
```

## Example docker-compose.yml

The `Dockerfile` in this project is designed to work with `docker-compose.yml` in this format.

- Ports to be exposed are controlled from the `docker-compose`.
- Entrypoint is also controlled from `docker-compose`

The reason why this is done this way is to have the env variables control from the
root, at compose level.

```yaml
services:
  nginx:
    restart: unless-stopped
    container_name: nginx
    build:
      context: ./src-nginx
      args:
        url_docker: ${url_docker_index}
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - web_static:/www/static
      - web_media:/www/media
    networks:
      - jf_net

  jetforge:
    restart: unless-stopped
    container_name: jetforge
    env_file:
      - ./src-jetforge/.env.prod
    build:
      context: ./src-jetforge
      args:
        url_pypi: ${url_pypi_index}
        url_docker: ${url_docker_index}
    ports:
      - ${JETFORGE_PORT}:${JETFORGE_PORT}
    networks:
      - jf_net
    entrypoint:
      - bash
      - "-c"
      - "gunicorn main.wsgi:application --bind 0.0.0.0:${JETFORGE_PORT}"

  mgdb:
    container_name: ${PROJECT_NAME}_mgdb
    restart: unless-stopped
    build:
      context: ./src_mgdb
      args:
        url_docker: ${url_docker_index}
    env_file:
      - ./src_mgdb/.env
    command: ["--bind_ip", "0.0.0.0", "--port", "${MGDB_PORT}"]
    ports:
      - "${MGDB_PORT}:${MGDB_PORT}"
    volumes:
      - mgdb_data:/data/db
      - ./src_mgdb/init-db.js:/docker-entrypoint-initdb.d/init-db.js:ro
    networks:
      - jf_net

networks:
  jf_net:
```
