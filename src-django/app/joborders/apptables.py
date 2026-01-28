import django_tables2 as djt
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django_tables2.paginators import LazyPaginator
from django_tables2.utils import A

from joborders import models

# Django Table DateTime format uses PHP-style
DJT_DT_FORMAT = "Y-m-d H:i"
DT_FORMAT = "%Y-%m-%d %H:%M"


class LeadingOrderTable(djt.Table):
    # id = djt.LinkColumn("joborders:undefined", args=[A("pk")])
    dt_engine_created = djt.DateTimeColumn(format=DJT_DT_FORMAT)
    dt_engine_stage = djt.DateTimeColumn(format=DJT_DT_FORMAT)
    dt_modified = djt.DateTimeColumn(format=DJT_DT_FORMAT)

    class Meta:
        model = models.LeadingOrderModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        exclude = ("changelog", "dt_created", "user_created", "ref_order", "is_active")
        per_page = 10

    def render_dt_engine_output(self, value):
        # Check if the datetime is in the future
        if value and value > timezone.now():
            return format_html(
                '<span style="color: blue;">{}</span>', value.strftime(DT_FORMAT)
            )
        return value.strftime(DT_FORMAT)
