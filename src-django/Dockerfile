ARG url_docker=docker.io
ARG url_pypi=https://pypi.org/simple/
FROM ${url_docker}/python:3.13.11-slim-trixie

ARG url_pypi
ENV url_pypi=${url_pypi}

WORKDIR /app
COPY ./app/ ./

COPY requirements.txt ./
RUN pip install -r ./requirements.txt --index-url ${url_pypi}

RUN chmod +x entrypoint-gunicorn.sh
RUN chmod +x entrypoint-celery.sh