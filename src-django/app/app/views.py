# app/views.py

# app/views.py
import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from app import appfilters, apptables, forms, models

lg = logging.getLogger("django")


class ConfigSettingsListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    model = models.ConfigSettingsModel
    table_class = apptables.ConfigSettingsTable
    filterset_class = appfilters.ConfigSettingsFilter
    template_name = "common/generic-list.html"
    permission_required = ["app.view_configsettingsmodel"]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.model.objects.all().order_by("-dt_modified")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Configurations"
        return context


class ConfigSettingsUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = models.ConfigSettingsModel
    form_class = forms.ConfigSettingsUpdateForm
    template_name = "app/config-update.html"
    permission_required = ["app.change_configsettingsmodel"]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Update Config: {self.object.name}"
        return context

    def form_valid(self, form):
        form.instance.user_modified = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("app:configsettings_detail", kwargs={"pk": self.object.pk})


class ConfigSettingsDetailView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = models.ConfigSettingsModel
    form_class = forms.ConfigSettingsDetailForm
    template_name = "app/config-update.html"
    permission_required = ["app.view_configsettingsmodel"]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"View Config: {self.object.name}"
        return context

    def post(self, *args, **kwargs):
        # disable POST method
        # we are using UpdateView here to make detail view easily
        return self.get(*args, **kwargs)


class ConfigSettingsDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = models.ConfigSettingsModel
    template_name = "common/generic-delete.html"
    permission_required = ["app.delete_configsettingsmodel"]
    success_url = reverse_lazy("app:configsettings_list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Delete Configuration"
        context["cancel_url"] = reverse_lazy(
            "app:configsettings_detail", kwargs={"pk": self.object.pk}
        )
        return context
