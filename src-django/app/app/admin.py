# app/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import JSONField
from django_json_widget.widgets import JSONEditorWidget

from app import models

UserModel = get_user_model()


@admin.register(models.ConfigSettingsModel)
class ConfigSettingsModelAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget},
    }
