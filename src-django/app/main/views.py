# main/views.py

from django.views.generic.base import TemplateView


class LandingPageView(TemplateView):
    template_name = "landing.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        return context


class DashboardView(TemplateView):
    template_name = "main/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "PPCS Dashboard"
        return context
