# joborders/models.py
import logging

from django.contrib.auth import get_user_model
from django.db import models

lg = logging.getLogger("django")


User = get_user_model()


class TemplateModel(models.Model):
    dt_created = models.DateTimeField(auto_now_add=True)
    dt_modified = models.DateTimeField(auto_now=True)
    changelog = models.JSONField(default=list)

    class Meta:
        abstract = True


class ReferenceOrderModel(TemplateModel):
    """
    Data model used reference to vendor/customer Order records.
    For example, STATCO order number, RSAF order number, etc.
    """

    uuid = models.CharField(max_length=256, unique=True)
    ro_number = models.CharField(max_length=64)
    ro_customer_name = models.CharField(max_length=256, null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    user_created = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reference_order_created",
    )
    user_modified = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reference_order_modified",
    )

    def __str__(self):
        return f"RO-{self.ro_number}"


class LeadingOrderModel(TemplateModel):
    """
    Data model used for creating Leading Order records.
    Synced with SAP.
    """

    ev_lo_number = models.CharField(max_length=64)
    ev_ref_order = models.ForeignKey(
        "ReferenceOrderModel",
        on_delete=models.PROTECT,
        related_name="leading_orders",
        blank=True,
        null=True,
    )
    engine = models.OneToOneField(
        "engines.EngineInstanceModel",
        on_delete=models.PROTECT,
        related_name="leading_order",
        blank=True,
        null=True,
    )
    customer = models.OneToOneField(
        "customers.EngineCustomerModel",
        on_delete=models.PROTECT,
        related_name="leading_order",
        blank=True,
        null=True,
    )
    sales = models.OneToOneField(
        "sales.SalesModel",
        on_delete=models.PROTECT,
        related_name="leading_order",
        blank=True,
        null=True,
    )
    operations = models.OneToOneField(
        "operations.OrderOperationsModel",
        on_delete=models.PROTECT,
        related_name="leading_order",
        blank=True,
        null=True,
    )

    ev_status = models.CharField(max_length=32, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    ev_job_type = models.CharField(max_length=128, null=True, blank=True)
    ev_reason_for_input = models.TextField(null=True, blank=True)

    ev_dt_engine_created = models.DateTimeField(null=True, blank=True)
    ev_dt_engine_stage = models.DateTimeField(null=True, blank=True)
    ev_dt_engine_output = models.DateTimeField(null=True, blank=True)
    user_created = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leading_order_created",
    )
    user_modified = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leading_order_modified",
    )

    def __str__(self):
        esn = self.engine.esn if self.engine else "N/A"
        return f"ESN-{esn}::LO-{self.ev_lo_number}"
