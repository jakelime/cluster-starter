# engines/models.py
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


class EngineMakeModel(TemplateModel):
    uuid = models.CharField(max_length=512, unique=True)
    make = models.CharField(max_length=64, null=True, blank=True)  # SAFRAN
    series = models.CharField(max_length=64, null=True, blank=True)  # CFM56 / LEAP
    model = models.CharField(max_length=64, null=True, blank=True)  # CFM56-5B / LEAP-1A
    submodel = models.CharField(max_length=128, null=True, blank=True)  # CFM56-5B4/3
    description = models.CharField(max_length=256, null=True, blank=True)
    user_created = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engine_make_created",
    )
    user_modified = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engine_make_modified",
    )

    def __str__(self):
        return f"{self.uuid}"


class EngineInstanceModel(TemplateModel):
    make = models.ForeignKey("EngineMakeModel", on_delete=models.PROTECT)
    config = models.CharField(max_length=64, null=True, blank=True)
    esn = models.CharField(max_length=128, null=True, blank=True)
    tsn = models.CharField(max_length=128, null=True, blank=True)  # time since new
    tso = models.CharField(max_length=128, null=True, blank=True)  # time since overhaul
    csn = models.CharField(max_length=128, null=True, blank=True)  # cycles since new
    cslv = models.CharField(
        max_length=128, null=True, blank=True
    )  # cycles since last visit
    thrust_rating = models.IntegerField(null=True, blank=True)
    is_engine_module = models.BooleanField(default=False)
    module = models.CharField(max_length=128, null=True, blank=True)
    user_created = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engine_instance_created",
    )
    user_modified = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engine_instance_modified",
    )

    def __str__(self):
        pk = self.pk if self.pk else "na"
        pk_str = str(pk)[-5:]
        return f"{self.esn}::{pk_str}"


class EnginePartModel(TemplateModel):
    part_number = models.CharField(max_length=64)
    description = models.CharField(max_length=256)
    uid = models.CharField(max_length=512, unique=True)
    user_created = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engine_part_created",
    )
    user_modified = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engine_part_modified",
    )

    def __str__(self):
        return self.uid

    def generate_uid(self) -> str:
        part_number = convert_to_snake_case(str(self.part_number))
        descr = convert_to_snake_case(self.description)
        return f"{part_number}::{descr}"

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = self.generate_uid()
        return super().save(*args, **kwargs)
