# app/urls.py
from django.urls import path
from app import views

app_name = "app"

urlpatterns = [
    path(
        "configs/", views.ConfigSettingsListView.as_view(), name="configsettings_list"
    ),
    path(
        "configs/<str:pk>/",
        views.ConfigSettingsDetailView.as_view(),
        name="configsettings_detail",
    ),
    path(
        "configs/<str:pk>/update/",
        views.ConfigSettingsUpdateView.as_view(),
        name="configsettings_update",
    ),    
    path(
        "configs/<str:pk>/delete/",
        views.ConfigSettingsDeleteView.as_view(),
        name="configsettings_delete",
    ),
]
