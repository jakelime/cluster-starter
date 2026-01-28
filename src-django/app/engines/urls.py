# engines/urls.py
from django.urls import path

from engines import views

app_name = "engines"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path(
        "engine-instances/",
        views.EngineInstanceListView.as_view(),
        name="ei_list",
    ),
]
