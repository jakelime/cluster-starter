# sales/models.py
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

lg = logging.getLogger("django")
SALES_CONF = settings.SALES_CONF


User = get_user_model()


class TemplateModel(models.Model):
    dt_created = models.DateTimeField(auto_now_add=True)
    dt_modified = models.DateTimeField(auto_now=True)
    changelog = models.JSONField(default=list)

    class Meta:
        abstract = True


class SalesModel(TemplateModel):
    """
    Data model used for tracking sales, finance and accounting related information.
    Tied to LeadingOrderModel.
    """

    # TODO: after adding all fields from sales file relevant to the above goal,
    # consider renaming/removing/adding fields as targets for the transform function to satisfy.
    uuid = models.CharField(max_length=256, unique=True)
    salesperson = models.CharField(max_length=64, null=True, blank=True)
    program_type = models.CharField(max_length=64, null=True, blank=True)
    est_sales_us = models.FloatField(null=True, blank=True)
    bid_status = models.CharField(max_length=64, null=True, blank=True)
    approved_gp_during_bid = models.FloatField(null=True, blank=True)
    prelim_cost_day_35_review_conducted_y_n = models.CharField(
        max_length=5, null=True, blank=True
    )  # TODO: map to boolean? how to handle "NA"?
    final_cost_1_day_before_testing_review_conducted_y_n = models.CharField(
        max_length=5, null=True, blank=True
    )  # TODO: map to boolean? how to handle "NA"?
    sales_recognition_status = models.CharField(max_length=64, null=True, blank=True)
    fct_sales_value = models.FloatField(null=True, blank=True)
    actual_sales_value = models.FloatField(null=True, blank=True)
    fct_cost = models.FloatField(null=True, blank=True)
    actual_cost = models.FloatField(null=True, blank=True)
    fct_gp = models.FloatField(null=True, blank=True)
    actual_gp = models.FloatField(null=True, blank=True)
    gp_percent = models.FloatField(null=True, blank=True)
    poc_effect = models.CharField(
        max_length=10, null=True, blank=True
    )  # TODO: map to boolean? how to handle "NA"?
    poc_cost_mark_up = models.FloatField(null=True, blank=True)
    poc_sales_b_f = models.FloatField(null=True, blank=True)
    poc_cost_b_f = models.FloatField(null=True, blank=True)
    poc = models.FloatField(null=True, blank=True)
    # We don't transform or store the monthly poc values since these are all computed based on the above inputs.

    user_created = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales_record_created",
    )
    user_modified = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales_record_modified",
    )

    def __str__(self):
        return f"UUID-{self.uuid}"
    
    class Meta(TemplateModel.Meta):
        indexes = [
            models.Index(fields=["uuid"]),
            models.Index(fields=["salesperson"]),
            models.Index(fields=["program_type"]),
            models.Index(fields=["bid_status"]),
        ]

    # TODO: create monthly poc calc functions and other derived value functions here
