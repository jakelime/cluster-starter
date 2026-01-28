# sales/urls.py
from django.urls import path

from sales import views

app_name = "sales"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("list/", views.SalesListView.as_view(), name="sales_list"),
    path("detail/<str:uuid>/", views.sales_detail_modal, name="detail_modal"),
    path("toggle-redaction/", views.toggle_redaction, name="toggle_redaction"),
]