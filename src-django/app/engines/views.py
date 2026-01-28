# engines/views.py

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import RedirectView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from engines import appfilters, apptables, models


class HomeView(RedirectView):
    pattern_name = "engines:ei_list"

    # This makes it a 302 (Temporary) redirect.
    # Safe for changes, doesn't get stuck in browser cache.
    permanent = False
    query_string = True


class EngineInstanceListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    model = models.EngineInstanceModel
    table_class = apptables.EngineInstanceTable
    filterset_class = appfilters.EngineInstanceFilter
    template_name = "common/generic-list.html"
    permission_required = ["engines.view_engineinstancemodel"]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.model.objects.all().order_by("-dt_modified")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Engine Instances"
        return context
