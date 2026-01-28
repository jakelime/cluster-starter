# main/urls.py
import logging

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from main import views

lg = logging.getLogger("django")

urlpatterns = [
    path("", views.LandingPageView.as_view(), name="landing"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("admin/", admin.site.urls),
    path("creds/", include("creds.urls")),
    path("connectors/", include("recon.urls")),
]

for app_name in settings.APP_MODULES:
    lg.debug(f"setting urls routing for {app_name}...")
    urlpatterns.append(path(f"{app_name}/", include(f"{app_name}.urls"), name=app_name))

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
