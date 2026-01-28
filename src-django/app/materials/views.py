from django.shortcuts import render
from django.views.generic.base import TemplateView, View
from recon.views import (
    Zmmr3010ReportCreateView,
    Zmmr3010ReportListView,
    Zmmr3010ReportUpdateView,
)


class HomeView(TemplateView):
    template_name = "materials/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Materials Management"
        return context


class MaterialsZmmrReportListView(Zmmr3010ReportListView):
    template_name = "materials/zmmr3010-list.html"


class MaterialsZmmrReportCreateView(Zmmr3010ReportCreateView):
    template_name = "materials/zmmr3010-create.html"
