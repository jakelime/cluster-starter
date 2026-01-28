# operations/urls.py
from django.urls import path

from operations import views

app_name = "operations"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    # path(
    #     "leading-orders/",
    #     views.LeadingOrderListView.as_view(),
    #     name="lo_list",
    # ),
]