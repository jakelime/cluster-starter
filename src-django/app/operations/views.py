# jetforge/recon/views.py
import logging

from django.conf import settings
from django.views.generic.base import TemplateView

lg = logging.getLogger("django")
MATR_CONF = settings.MATR_CONF

class HomeView(TemplateView):
    template_name = "operations/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Operations"
        return context