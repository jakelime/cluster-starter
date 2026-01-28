import django_tables2 as djt
from sales.templatetags.sales_extras import should_redact
from sales import models


class SalesTable(djt.Table):
    class PercentageColumn(djt.Column):
        def render(self, value):
            if value is None:
                return None
            return f"{value * 100:.2f}%"
        
    class RedactableCurrencyColumn(djt.Column):
        def render(self, value, table):
            if value is None:
                return None
            if hasattr(table, 'request') and should_redact(table.request):
                return "$XXX.XX"
            return f"${value:,.2f}"

    # Operations columns
    esn = djt.Column(verbose_name="ESN")
    customer = djt.Column(verbose_name="Customer")
    status = djt.Column(verbose_name="Status")
    engine_type = djt.Column(verbose_name="Engine Type")
    facility = djt.Column(verbose_name="Facility")
    certainty_of_engine_input = djt.Column(verbose_name="Certainty of Engine Input")

    # Dates
    dt_input_target = djt.DateColumn(format="Y-m-d", verbose_name="Input Date (Tgt)")
    dt_input_actual = djt.DateColumn(format="Y-m-d", verbose_name="Input Date (Act)")
    dt_induction_target = djt.DateColumn(
        format="Y-m-d", verbose_name="Induction Date (Tgt)"
    )
    dt_induction_actual = djt.DateColumn(
        format="Y-m-d", verbose_name="Induction Date (Act)"
    )
    dt_shipment_target = djt.DateColumn(
        format="Y-m-d", verbose_name="Shipment Date (Tgt)"
    )
    dt_shipment_actual = djt.DateColumn(
        format="Y-m-d", verbose_name="Shipment Date (Act)"
    )
    engine_output_forecast_month = djt.DateColumn(
        format="Y-m", verbose_name="Output Forecast Month"
    )

    # Sales columns
    uuid = djt.TemplateColumn(
        template_code="""
            <a href="#" 
               class="text-primary text-decoration-underline" 
               data-bs-toggle="modal" 
               data-bs-target="#detailModal"
               hx-get="{% url 'sales:detail_modal' record.uuid %}"
               hx-target="#detailModalContent"
               hx-trigger="click"
               hx-push-url="false">
               {{ record.uuid }}
            </a>
        """,
        verbose_name="UUID",
    )
    salesperson = djt.Column(verbose_name="Salesperson")
    program_type = djt.Column(verbose_name="Program Type")
    est_sales_us = RedactableCurrencyColumn(verbose_name="Estimated Sales (US$)")
    bid_status = djt.Column(verbose_name="Bid Status")
    approved_gp_during_bid = PercentageColumn(verbose_name="Approved GP% During Bid")
    prelim_cost_day_35_review_conducted_y_n = djt.Column(
        verbose_name="Was Prelim Cost Review Conducted?"
    )
    final_cost_1_day_before_testing_review_conducted_y_n = djt.Column(
        verbose_name="Was Final Cost Review Conducted?"
    )
    sales_recognition_status = djt.Column(verbose_name="Sales Recognition Status")
    fct_sales_value = RedactableCurrencyColumn(verbose_name="Forecast Sales Value (US$)")
    actual_sales_value = RedactableCurrencyColumn(verbose_name="Actual Sales Value (US$)")
    fct_cost = RedactableCurrencyColumn(verbose_name="Forecast Cost (US$)")
    actual_cost = RedactableCurrencyColumn(verbose_name="Actual Cost (US$)")
    fct_gp = RedactableCurrencyColumn(verbose_name="Forecast GP (US$)")
    actual_gp = RedactableCurrencyColumn(verbose_name="Actual GP (US$)")
    gp_percent = PercentageColumn(verbose_name="GP%")
    poc_effect = djt.Column(verbose_name="POC Effect")
    poc_cost_mark_up = RedactableCurrencyColumn(verbose_name="POC Cost Mark-Up (US$)")
    poc_sales_b_f = RedactableCurrencyColumn(verbose_name="POC Sales B/F (US$)")
    poc_cost_b_f = RedactableCurrencyColumn(verbose_name="POC Cost B/F (US$)")
    poc = PercentageColumn(verbose_name="POC %")

    class Meta:
        model = models.SalesModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = (
            "uuid",
            "esn",
            "customer",
            "program_type",
            "status",
            "engine_type",
            "facility",
            "certainty_of_engine_input",
            "dt_input_target",
            "dt_input_actual",
            "dt_induction_target",
            "dt_induction_actual",
            "dt_shipment_target",
            "dt_shipment_actual",
            "engine_output_forecast_month",
            "salesperson",
            "est_sales_us",
            "bid_status",
            "approved_gp_during_bid",
            "prelim_cost_day_35_review_conducted_y_n",
            "final_cost_1_day_before_testing_review_conducted_y_n",
            "sales_recognition_status",
            "fct_sales_value",
            "actual_sales_value",
            "fct_cost",
            "actual_cost",
            "fct_gp",
            "actual_gp",
            "gp_percent",
            "poc_effect",
            "poc_cost_mark_up",
            "poc_sales_b_f",
            "poc_cost_b_f",
            "poc",
        )
