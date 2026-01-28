from django import forms
from sales import models as sales_models
from operations import models as ops_models


class SalesEditForm(forms.ModelForm):
    template_name = "common/partials/form-bootstrap5-toggle.html"

    class Meta:
        model = sales_models.SalesModel
        fields = [
            "salesperson",
            "program_type",
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
        ]
        labels = {
            "salesperson": "Salesperson",
            "program_type": "Program Type",
            "est_sales_us": "Estimated Sales (US$)",
            "bid_status": "Bid Status",
            "approved_gp_during_bid": "Approved GP% During Bid",
            "prelim_cost_day_35_review_conducted_y_n": "Was Prelim Cost Review Conducted?",
            "final_cost_1_day_before_testing_review_conducted_y_n": "Was Final Cost Review Conducted?",
            "sales_recognition_status": "Sales Recognition Status",
            "fct_sales_value": "Forecast Sales Value (US$)",
            "actual_sales_value": "Actual Sales Value (US$)",
            "fct_cost": "Forecast Cost (US$)",
            "actual_cost": "Actual Cost (US$)",
            "fct_gp": "Forecast GP (US$)",
            "actual_gp": "Actual GP (US$)",
            "gp_percent": "GP%",
            "poc_effect": "POC Effect",
            "poc_cost_mark_up": "POC Cost Mark-Up (US$)",
            "poc_sales_b_f": "POC Sales B/F (US$)",
            "poc_cost_b_f": "POC Cost B/F (US$)",
            "poc": "POC (US$)",
        }


class OperationsEditForm(forms.ModelForm):
    template_name = "common/partials/form-bootstrap5-toggle.html"

    class Meta:
        model = ops_models.OrderOperationsModel
        fields = [
            "esn",
            "customer",
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
            "engine_output_forecast_month_see_note_for_lion_air",
        ]
        labels = {
            "esn": "ESN",
            "customer": "Customer",
            "status": "Status",
            "engine_type": "Engine Type",
            "facility": "Facility",
            "certainty_of_engine_input": "Certainty of Engine Input",
            "dt_input_target": "Input Date (Target)",
            "dt_input_actual": "Input Date (Actual)",
            "dt_induction_target": "Induction Date (Target)",
            "dt_induction_actual": "Induction Date (Actual)",
            "dt_shipment_target": "Shipment Date (Target)",
            "dt_shipment_actual": "Shipment Date (Actual)",
            "engine_output_forecast_month_see_note_for_lion_air": (
                "Output Forecast Month"
            ),
        }
        widgets = {
            "dt_input_target": forms.DateInput(attrs={"type": "date"}),
            "dt_input_actual": forms.DateInput(attrs={"type": "date"}),
            "dt_induction_target": forms.DateInput(attrs={"type": "date"}),
            "dt_induction_actual": forms.DateInput(attrs={"type": "date"}),
            "dt_shipment_target": forms.DateInput(attrs={"type": "date"}),
            "dt_shipment_actual": forms.DateInput(attrs={"type": "date"}),
            "engine_output_forecast_month_see_note_for_lion_air": forms.DateInput(
                attrs={"type": "date"}
            ),
        }
