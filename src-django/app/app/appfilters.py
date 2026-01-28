# app/appfilters.py
from django_filters import FilterSet

from app import models


class ConfigSettingsFilter(FilterSet):
    class Meta:
        model = models.ConfigSettingsModel
        fields = {
            "name": ["icontains"],
        }
