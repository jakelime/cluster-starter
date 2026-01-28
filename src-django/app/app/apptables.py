# app/apptables.py
import django_tables2 as djt

from app import models

# Django Table DateTime format uses PHP-style
DJT_DT_FORMAT = "Y-m-d H:i"
DT_FORMAT = "%Y-%m-%d %H:%M"


class ConfigSettingsTable(djt.Table):
    id = djt.Column(linkify=True)
    dt_modified = djt.DateTimeColumn(format=DJT_DT_FORMAT)

    class Meta:
        model = models.ConfigSettingsModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = ("id", "name", "user_created", "dt_created")
        # exclude = ("config", "dt_created", "changelog", "user_created")
        per_page = 10
