# customers/urls.py
from django.urls import path

from customers import views

app_name = "customers"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
]
