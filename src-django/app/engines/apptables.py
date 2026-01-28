import django_tables2 as djt

from engines import models

# Django Table DateTime format uses PHP-style
DJT_DT_FORMAT = "Y-m-d H:i"
DT_FORMAT = "%Y-%m-%d %H:%M"


class EngineInstanceTable(djt.Table):
    dt_created = djt.DateTimeColumn(format=DJT_DT_FORMAT)
    dt_modified = djt.DateTimeColumn(format=DJT_DT_FORMAT)

    class Meta:
        model = models.EngineInstanceModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        exclude = ("changelog", "dt_created", "user_created", "ref_order", "is_active")
        per_page = 10
