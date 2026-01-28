from django.apps import AppConfig


class EnginesConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'engines'
