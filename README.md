# Starter Repo for building K8s Clusters

A "simple" cluster might start with these services:

- webapp (nginx)
- app (python-django)
- frontend app (js-react)
- tasks (python-celery)
- db (mongodb)
- cache (redis)

This repo have basic hello-world services to test deployment
to aws EKS, or also other cloud services.

## Helper functions

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(15)).decode('utf-8').replace('-', '').replace('_', '').strip('=')[:20])"
python -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(15)).decode('utf-8').replace('-', '').replace('_', '').strip('=')[:20].lower())"
```
