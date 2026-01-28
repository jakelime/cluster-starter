# jetforge/recon/views.py
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import OuterRef, Subquery, DateTimeField
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic.base import RedirectView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from operations.models import OrderOperationsModel
from sales import appfilters, apptables, models
from sales import forms as sales_forms

lg = logging.getLogger("django")
MATR_CONF = settings.MATR_CONF


class HomeView(RedirectView):
    pattern_name = "sales:sales_list"

    # This makes it a 302 (Temporary) redirect.
    # Safe for changes, doesn't get stuck in browser cache.
    permanent = False
    query_string = True


class SalesListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    model = models.SalesModel
    table_class = apptables.SalesTable
    filterset_class = appfilters.SalesFilter
    template_name = "sales/sales-list.html"
    permission_required = ["sales.view_salesmodel"]
    paginate_by = 15

    def get_template_names(self):
        # HTMX support: return only the table partial if requested by HTMX
        if self.request.htmx:
            return ["sales/partials/sales-list-table.html"]
        return [self.template_name]

    def get_queryset(self):
        # Prepare subquery to Ops model linked by UUID
        ops = OrderOperationsModel.objects.filter(sales_uuid=OuterRef("uuid"))

        # Annotate SalesModel with fields from OrderOperationsModel
        queryset = models.SalesModel.objects.annotate(
            facility=Subquery(ops.values("facility")[:1]),
            certainty_of_engine_input=Subquery(
                ops.values("certainty_of_engine_input")[:1]
            ),
            engine_output_forecast_month=Subquery(
                ops.values("engine_output_forecast_month_see_note_for_lion_air")[:1]
            ),
            esn=Subquery(ops.values("esn")[:1]),
            engine_type=Subquery(ops.values("engine_type")[:1]),
            customer=Subquery(ops.values("customer")[:1]),
            status=Subquery(ops.values("status")[:1]),
            dt_input_target=Subquery(
                ops.values("dt_input_target")[:1], output_field=DateTimeField()
            ),
            dt_input_actual=Subquery(
                ops.values("dt_input_actual")[:1], output_field=DateTimeField()
            ),
            dt_induction_target=Subquery(
                ops.values("dt_induction_target")[:1], output_field=DateTimeField()
            ),
            dt_induction_actual=Subquery(
                ops.values("dt_induction_actual")[:1], output_field=DateTimeField()
            ),
            dt_shipment_target=Subquery(
                ops.values("dt_shipment_target")[:1], output_field=DateTimeField()
            ),
            dt_shipment_actual=Subquery(
                ops.values("dt_shipment_actual")[:1], output_field=DateTimeField()
            ),
        ).order_by("uuid")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sales List"
        return context


def sales_detail_modal(request, uuid):
    """
    View to handle the sales detail modal.
    This is used by HTMX to fetch the sales detail for a specific UUID.
    """

    # Retrieve sales record
    try:
        sales_record = models.SalesModel.objects.get(uuid=uuid)
    except models.SalesModel.DoesNotExist:
        lg.error(f"Sales record with UUID {uuid} does not exist.")
        return RedirectView.as_view(pattern_name="sales:sales_list")(request)
    
    is_editing = request.GET.get("mode") == "edit"

    # Retrieve operations record via uuid (loosely coupled)
    try:
        ops_record = OrderOperationsModel.objects.get(sales_uuid=uuid)
    except OrderOperationsModel.DoesNotExist:
        ops_record = None  # Handle the case where no operations record exists

    if request.method == "POST":
        is_editing = True
        sales_form = sales_forms.SalesEditForm(
            request.POST, instance=sales_record, prefix="sales"
        )
        ops_form = (
            sales_forms.OperationsEditForm(
                request.POST, instance=ops_record, prefix="ops"
            )
            if ops_record
            else None
        )

        if sales_form.is_valid() and (ops_form is None or ops_form.is_valid()):
            sales_form.save()
            if ops_form:
                ops_form.save()

            messages.success(request, f"Sales record {uuid} updated successfully.")
            lg.info(f"Sales record {uuid} updated successfully.")

            response = HttpResponse(
                content="Sales record updated successfully.",
                status=200,
            )
            response["HX-Refresh"] = "true"  # Refresh the page after saving
            is_editing = False # Switch back to view mode
            return response
        else:
            messages.error(request, "Failed to save. Please contact an administrator for assistance.")
    else:
        sales_form = sales_forms.SalesEditForm(instance=sales_record, prefix="sales")
        ops_form = (
            sales_forms.OperationsEditForm(instance=ops_record, prefix="ops")
            if ops_record
            else None
        )
    context = {
        "sales_record": sales_record,
        "ops_record": ops_record,
        "page_title": f"Sales Detail - {sales_record.uuid}",
        "sales_form": sales_form,
        "ops_form": ops_form,
        "is_editing": is_editing,
        "request": request,
    }

    return render(request, "sales/partials/sales-detail-modal.html", context)

def toggle_redaction(request):
    """
    Toggle the redaction state for the current user.
    This is used to show/hide sensitive information in sales records.
    """
    current_state = request.session.get("hide_financials", False)
    request.session["hide_financials"] = not current_state

    # Redirect back to the referring page or sales list if no referrer
    return redirect(request.META.get("HTTP_REFERER", "sales:sales_list"))
