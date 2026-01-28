# app/models.py
import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

lg = logging.getLogger("django")


User = get_user_model()


class TemplateModel(models.Model):
    dt_created = models.DateTimeField(auto_now_add=True)
    dt_modified = models.DateTimeField(auto_now=True)
    changelog = models.JSONField(default=list)

    class Meta:
        abstract = True


class ConfigSettingsModel(TemplateModel):
    """
    Data model to store user-configurable configurations
    dynamically.

    Records using this model should always be called using
    Django ORM `objects.get_or_create()`, with hard-coded
    default values.
    """

    name = models.CharField(max_length=64, unique=True)
    config = models.JSONField(null=True, blank=True)

    user_created = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="configs_created",
    )
    user_modified = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="configs_modified",
    )

    def __str__(self):
        return f"config.{self.name}"

    def get_absolute_url(self):
        return reverse("app:configsettings_detail", kwargs={"pk": self.pk})

    def get_list_url(self):
        return reverse("app:configsettings_list")

    def get_update_url(self):
        return reverse("app:configsettings_update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse("app:configsettings_delete", kwargs={"pk": self.pk})
