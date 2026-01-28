# customers/models.py
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from main.utils import convert_to_snake_case

lg = logging.getLogger("django")
MATR_CONF = settings.MATR_CONF


User = get_user_model()


class TemplateModel(models.Model):
    dt_created = models.DateTimeField(auto_now_add=True)
    dt_modified = models.DateTimeField(auto_now=True)
    changelog = models.JSONField(default=list)

    class Meta:
        abstract = True


class EngineCustomerModel(TemplateModel):
    code = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=128, null=True, blank=True)
    name_short = models.CharField(max_length=64, null=True, blank=True)
    user_created = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engine_customer_created",
    )
    user_modified = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engine_customer_modified",
    )

    def __str__(self):
        return self.code
