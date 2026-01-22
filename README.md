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

# Generates a secured secret key for use as password of 1+21 char in length
# The first char is always a letter, no dash and underscore for easy copypaste and url-safe.
## 22 chars password
python -c "import secrets, string; alph = string.ascii_letters + string.digits; print(secrets.choice(string.ascii_letters) + ''.join(secrets.choice(alph) for _ in range(21)))"
## 32 chars password
python -c "import secrets, string; alph = string.ascii_letters + string.digits; print(secrets.choice(string.ascii_letters) + ''.join(secrets.choice(alph) for _ in range(31)))"

# Generates a secret key
## 32 chars
python -c "import secrets; print(secrets.token_urlsafe(32)[:32])"
```
