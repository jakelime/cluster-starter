from django.contrib import admin

from recon import models


@admin.register(models.Zmmr3010ReportModel)
class Zmmr3010ReportModelAdmin(admin.ModelAdmin):
    list_display = ["name", "pk", "task_id", "dt_created", "status", "is_deleted"]
    search_fields = ["status", "name", "task_id", "result"]


# 1. Register Concrete File Upload Models (other defaults)
admin.site.register(models.LeadingOrderFileUploadModel)
admin.site.register(models.SalesFileUploadModel)
admin.site.register(models.OpsFileUploadModel)

# 2. Register Transform/Task Models
admin.site.register(models.LeadingOrderTransformModel)
admin.site.register(models.SalesTransformModel)
