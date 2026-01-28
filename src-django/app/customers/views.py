# customers/views.py

from django.views.generic.base import TemplateView


class HomeView(TemplateView):
    template_name = "customers/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Customers HomeView"
        return context
