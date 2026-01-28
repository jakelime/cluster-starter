# operations/models.py
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

lg = logging.getLogger("django")
OPS_CONF = settings.OPS_CONF


User = get_user_model()


class TemplateModel(models.Model):
    dt_created = models.DateTimeField(auto_now_add=True)
    dt_modified = models.DateTimeField(auto_now=True)
    changelog = models.JSONField(default=list)

    class Meta:
        abstract = True


class OrderOperationsModel(TemplateModel):
    """
    Data model used for tracking operations related information for a given job order.
    Tied to LeadingOrderModel.
    """

    # fields from sales file
    sales_uuid = models.CharField(max_length=256, unique=True)
    facility = models.CharField(max_length=64, null=True, blank=True)
    certainty_of_engine_input = models.CharField(max_length=64, null=True, blank=True)
    engine_output_forecast_month_see_note_for_lion_air = models.DateTimeField(
        null=True, blank=True
    )

    # fields from ops file
    esn = models.CharField(max_length=64, null=True, blank=True)
    module_sn = models.CharField(max_length=64, null=True, blank=True)
    engine_type = models.CharField(max_length=64, null=True, blank=True)
    engine_model = models.CharField(max_length=64, null=True, blank=True)
    customer = models.CharField(max_length=128, null=True, blank=True)
    operator = models.CharField(max_length=128, null=True, blank=True)
    job_number = models.CharField(max_length=64, null=True, blank=True)
    shop_visit_scope = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=64, null=True, blank=True)
    dt_input_target = models.DateTimeField(null=True, blank=True)
    dt_input_actual = models.DateTimeField(null=True, blank=True)
    dt_induction_target = models.DateTimeField(null=True, blank=True)
    dt_induction_actual = models.DateTimeField(null=True, blank=True)
    dt_gate_1_target = models.DateTimeField(null=True, blank=True)
    dt_gate_1_actual = models.DateTimeField(null=True, blank=True)
    dt_gate_1a_target = models.DateTimeField(null=True, blank=True)
    dt_gate_1a_actual = models.DateTimeField(null=True, blank=True)
    dt_gate_1b_target = models.DateTimeField(null=True, blank=True)
    dt_gate_1b_actual = models.DateTimeField(null=True, blank=True)
    dt_gate_2_kitting_target = models.DateTimeField(null=True, blank=True)
    dt_gate_2_kitting_actual = models.DateTimeField(null=True, blank=True)
    dt_rigging_target = models.DateTimeField(null=True, blank=True)
    dt_rigging_actual = models.DateTimeField(null=True, blank=True)
    dt_gate_3_target = models.DateTimeField(null=True, blank=True)
    dt_gate_3_actual = models.DateTimeField(null=True, blank=True)
    dt_gate_3a_target = models.DateTimeField(null=True, blank=True)
    dt_gate_3a_actual = models.DateTimeField(null=True, blank=True)
    dt_gate_3b_target = models.DateTimeField(null=True, blank=True)
    dt_gate_3b_actual = models.DateTimeField(null=True, blank=True)
    dt_pass_test_target = models.DateTimeField(null=True, blank=True)
    dt_pass_test_actual = models.DateTimeField(null=True, blank=True)
    dt_pack_ready_target = models.DateTimeField(null=True, blank=True)
    dt_pack_ready_actual = models.DateTimeField(null=True, blank=True)
    dt_shipment_target = models.DateTimeField(null=True, blank=True)
    dt_shipment_actual = models.DateTimeField(null=True, blank=True)
    dt_delivered_to_customer_target = models.DateTimeField(null=True, blank=True)
    dt_delivered_to_customer_actual = models.DateTimeField(null=True, blank=True)
    key_issues_impacting_tat = models.CharField(max_length=256, null=True, blank=True)
    remarks = models.CharField(max_length=256, null=True, blank=True)

    user_created = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operations_record_created",
    )
    user_modified = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operations_record_modified",
    )

    def __str__(self):
        return f"ESN-{self.esn}::UUID-{self.sales_uuid}"
    
    class Meta(TemplateModel.Meta):
        indexes = [
            models.Index(fields=["sales_uuid"]),
            models.Index(fields=["facility"]),
            models.Index(fields=["certainty_of_engine_input"]),
            models.Index(fields=["esn"]),
            models.Index(fields=["engine_type"]),
            models.Index(fields=["engine_model"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["operator"]),
            models.Index(fields=["job_number"]),
            models.Index(fields=["status"]),
        ]