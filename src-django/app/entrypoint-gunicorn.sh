#!/bin/bash

python manage.py makemigrations creds --noinput
python manage.py makemigrations recon --noinput
python manage.py makemigrations customers --noinput
python manage.py makemigrations joborders --noinput
python manage.py makemigrations operations --noinput
python manage.py makemigrations sales --noinput
python manage.py migrate --noinput
python manage.py init_superuser 
# python manage.py init_data
python manage.py collectstatic --noinput

# set workers=4 in DEV
# set workers=6 in UAT/PROD
gunicorn main.asgi:application \
  -k uvicorn_config.DjangoUvicornWorker \
  --bind "0.0.0.0:$1" \
  --workers 6 \
  --timeout 60
