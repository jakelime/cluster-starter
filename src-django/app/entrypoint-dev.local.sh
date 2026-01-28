#!/bin/bash

python manage.py makemigrations creds --noinput
python manage.py makemigrations recon --noinput
python manage.py makemigrations customers --noinput
python manage.py makemigrations joborders --noinput
python manage.py migrate --noinput
python manage.py init_superuser 

## Using uvicorn for development with auto-reload
uvicorn main.asgi:application --reload

## Using guicorn (typically for production)
## set workers=4 in DEV
## set workers=6 in UAT/PROD
# gunicorn main.asgi:application \
#   -k uvicorn_config.DjangoUvicornWorker \
#   --bind "127.0.0.1:8000" \
#   --workers 4 \
#   --timeout 60
