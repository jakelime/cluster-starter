from django.apps import AppConfig


class CustomersConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'customers'
