# recon/urls.py
from django.urls import path

from materials import views

app_name = "materials"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path(
        "zmmr3010/create/",
        views.MaterialsZmmrReportCreateView.as_view(),
        name="zmmr3010_create",
    ),
    path(
        "zmmr3010/",
        views.MaterialsZmmrReportListView.as_view(),
        name="zmmr3010_list",
    ),
]
