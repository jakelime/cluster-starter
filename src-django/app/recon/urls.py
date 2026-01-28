# recon/urls.py
from django.urls import path

from recon import views

app_name = "recon"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path(
        "celery/",
        views.CeleryTaskDetailView.as_view(),
        name="celery_task_detail",
    ),
    # [Extract Jobs] fileuploads :: Materials :: Zmmr3010
    path(
        "fileuploads/zmmr3010/<str:pk>/update/",
        views.Zmmr3010ReportUpdateView.as_view(),
        name="zmmr3010_update",
    ),
    path(
        "fileuploads/zmmr3010/<str:pk>/delete/",
        views.Zmmr3010ReportDeleteView.as_view(),
        name="zmmr3010_delete",
    ),
    path(
        "fileuploads/zmmr3010/<str:pk>/load/",
        views.load_zmmr3010_task_view,
        name="zmmr3010_load",
    ),
    path(
        "fileuploads/zmmr3010/create/",
        views.Zmmr3010ReportCreateView.as_view(),
        name="zmmr3010_create",
    ),
    path(
        "fileuploads/zmmr3010/",
        views.Zmmr3010ReportListView.as_view(),
        name="zmmr3010_list",
    ),
    # [Extract Jobs] fileuploads :: Materials?? :: LeadingOrders
    path(
        "fileuploads/leading-orders/<str:pk>/update/",
        views.LeadingOrderFileUploadUpdateView.as_view(),
        name="lo_fileupload_update",
    ),
    path(
        "fileuploads/leading-orders/<str:pk>/load/",
        views.load_lo_fileupload_task_view,
        name="lo_fileupload_load",
    ),
    path(
        "fileuploads/leading-orders/create/",
        views.LeadingOrderFileUploadCreateView.as_view(),
        name="lo_fileupload_create",
    ),
    path(
        "fileuploads/leading-orders/",
        views.LeadingOrderFileUploadListView.as_view(),
        name="lo_fileupload_list",
    ),
    # [Extract Jobs] fileuploads :: Sales Forecast Mgmt File
    path(
        "fileuploads/sales/<str:pk>/update/",
        views.SalesFileUploadUpdateView.as_view(),
        name="sales_fileupload_update",
    ),
    path(
        "fileuploads/sales/<str:pk>/load/",
        views.load_sales_fileupload_task_view,
        name="sales_fileupload_load",
    ),
    path(
        "fileuploads/sales/create/",
        views.SalesFileUploadCreateView.as_view(),
        name="sales_fileupload_create",
    ),
    path(
        "fileuploads/sales/",
        views.SalesFileUploadListView.as_view(),
        name="sales_fileupload_list",
    ),
    # [Extract Jobs] fileuploads :: Operations Planning Mgmt File
    path(
        "fileuploads/ops/<str:pk>/update/",
        views.OpsFileUploadUpdateView.as_view(),
        name="ops_fileupload_update",
    ),
    path(
        "fileuploads/ops/<str:pk>/load/",
        views.load_ops_fileupload_task_view,
        name="ops_fileupload_load",
    ),
    path(
        "fileuploads/ops/create/",
        views.OpsFileUploadCreateView.as_view(),
        name="ops_fileupload_create",
    ),
    path(
        "fileuploads/ops/",
        views.OpsFileUploadListView.as_view(),
        name="ops_fileupload_list",
    ),
    # List Tasks (Transform Jobs)
    path(
        "tasks/extract/leading-orders/",
        views.LeadingOrderTransformListView.as_view(),
        name="lo_transform_list",
    ),
    path(
        "tasks/extract/sales/",
        views.SalesTransformListView.as_view(),
        name="sales_transform_list",
    ),
    path(
        "tasks/extract/ops/",
        views.OpsTransformListView.as_view(),
        name="ops_transform_list",
    ),
    # Task Triggers
    path(
        "tasks/transform/leading-orders/trigger/",
        views.LeadingOrderTransformCreateView.as_view(),
        name="lo_transform_action",
    ),
    path(
        "tasks/transform/sales/trigger/",
        views.SalesTransformCreateView.as_view(),
        name="sales_transform_action",
    ),
    path(
        "tasks/transform/ops/trigger/",
        views.OpsTransformCreateView.as_view(),
        name="ops_transform_action",
    ),
    # Modular Home Views
    path(
        "materials/",
        views.MaterialsConnectorsView.as_view(),
        name="materials_connectors",
    ),
    path(
        "engines/",
        views.EnginesConnectorsView.as_view(),
        name="engines_connectors",
    ),
    path(
        "sales/",
        views.SalesConnectorsView.as_view(),
        name="sales_connectors",
    ),
    path(
        "ops/",
        views.OpsConnectorsView.as_view(),
        name="ops_connectors",
    ),
]
