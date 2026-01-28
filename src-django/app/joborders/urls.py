# joborders/urls.py
from django.urls import path

from joborders import views

app_name = "joborders"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path(
        "leading-orders/",
        views.LeadingOrderListView.as_view(),
        name="lo_list",
    ),
]
