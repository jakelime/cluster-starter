# jobrders/views.py
import logging

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import RedirectView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from joborders import appfilters, apptables, models

lg = logging.getLogger("django")


class HomeView(RedirectView):
    pattern_name = "joborders:lo_list"

    # This makes it a 302 (Temporary) redirect.
    # Safe for changes, doesn't get stuck in browser cache.
    permanent = False
    query_string = True


class LeadingOrderListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    model = models.LeadingOrderModel
    table_class = apptables.LeadingOrderTable
    filterset_class = appfilters.LeadingOrderFilter
    template_name = "common/generic-list.html"
    permission_required = ["engines.view_leadingordermodel"]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.model.objects.all().order_by("-ev_dt_engine_created")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "LeadingOrders"
        return context
