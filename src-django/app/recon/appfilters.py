from django_filters import FilterSet
from recon import models


class Zmmr3010ReportFilter(FilterSet):
    class Meta:
        model = models.Zmmr3010ReportModel
        fields = {
            "name": ["icontains"],
            "task_id": ["icontains"],
            "user_created__username": ["icontains"],
            "dt_created": ["lt", "gt"],
            "status": ["icontains"],
        }


class LeadingOrderFileUploadFilter(FilterSet):
    class Meta:
        model = models.LeadingOrderFileUploadModel
        fields = {
            "name": ["icontains"],
            "task_id": ["icontains"],
            "user_created__username": ["icontains"],
            "dt_created": ["lt", "gt"],
            "status": ["icontains"],
        }


class SalesFileUploadFilter(FilterSet):
    class Meta:
        model = models.SalesFileUploadModel
        fields = {
            "name": ["icontains"],
            "task_id": ["icontains"],
            "user_created__username": ["icontains"],
            "dt_created": ["lt", "gt"],
            "status": ["icontains"],
        }


class OpsFileUploadFilter(FilterSet):
    class Meta:
        model = models.OpsFileUploadModel
        fields = {
            "name": ["icontains"],
            "task_id": ["icontains"],
            "user_created__username": ["icontains"],
            "dt_created": ["lt", "gt"],
            "status": ["icontains"],
        }


class HelloListFilter(FilterSet):
    class Meta:
        model = models.HelloModel
        fields = {
            "name": ["icontains"],
            "task_id": ["icontains"],
            "user_created__username": ["icontains"],
            "dt_created": ["lt", "gt"],
            "status": ["icontains"],
        }
