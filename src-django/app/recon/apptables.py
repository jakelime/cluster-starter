import django_tables2 as djt
from django.urls import reverse
from django.utils.html import format_html
from django_tables2.utils import A

from recon import models

DT_FORMAT = "Y-m-d H:i"


def render_processing_time(value: float) -> str:
    if value > 120:
        minutes = value / 60
        if minutes > 60:
            hours = minutes / 60
            return f"{hours:.3f}hrs"
        return f"{minutes:.3f}mins"
    return f"{value:.3f}s"


class Zmmr3010ReportTable(djt.Table):
    per_page_field = 20
    dt_created = djt.DateTimeColumn(format=DT_FORMAT)
    output = djt.TemplateColumn(
        template_code='{% if record.get_output_name == "none" %}{{record.get_output_name}}{% elif record.get_output_name == "ParseExcelError" %}{{record.get_output_name}}{% else %}<a href="{{record.get_output_url}}">{{record.get_output_name}}</a>{% endif %}',
        template_name="output",
        orderable=False,
    )

    class Meta:
        model = models.Zmmr3010ReportModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = (
            "id",
            "dt_created",
            "user_created",
            "name",
            "status",
        )

    def render_processing_time(self, value):
        if value > 120:
            minutes = value / 60
            if minutes > 60:
                hours = minutes / 60
                return f"{hours:.3f}hrs"
            return f"{minutes:.3f}mins"
        return f"{value:.3f}s"


class Zmmr3010ReportActionTable(djt.Table):
    id = djt.LinkColumn("recon:zmmr3010_update", args=[A("pk")])
    per_page_field = 50
    dt_created = djt.DateTimeColumn(format=DT_FORMAT)
    input_ = djt.TemplateColumn(
        template_code='<a href="{{record.get_input_url}}">{{record.get_input_name}}</a>',
        template_name="input",
        orderable=False,
    )
    output = djt.TemplateColumn(
        template_code='{% if record.get_output_name == "none" %}{{record.get_output_name}}{% elif record.get_output_name == "ParseExcelError" %}{{record.get_output_name}}{% else %}<a href="{{record.get_output_url}}">{{record.get_output_name}}</a>{% endif %}',
        template_name="output",
        orderable=False,
    )
    delete_action = djt.Column(empty_values=(), orderable=False, verbose_name="Action")

    class Meta:
        model = models.Zmmr3010ReportModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = (
            "id",
            "dt_created",
            "name",
            "user_created",
            "status",
            "processing_time",
        )

    def render_id(self, value):
        """
        Renders the ID as a shortened string for display.
        'value' is the full MongoDB ID.
        """
        val_str = str(value)
        # Check if the string is long enough to shorten (3 + 3 dots + 5 = 11)
        if len(val_str) > 8:
            return f"{val_str[:3]}...{val_str[-5:]}"
        # Return as-is if it's not the expected length
        return val_str

    def render_processing_time(self, value):
        if value > 120:
            minutes = value / 60
            if minutes > 60:
                hours = minutes / 60
                return f"{hours:.3f}hrs"
            return f"{minutes:.3f}mins"
        return f"{value:.3f}s"

    def render_delete_action(self, record):
        return format_html(
            '<a href="{}" class="btn btn-sm btn-danger">Delete</a>',
            reverse("recon:zmmr3010_delete", kwargs={"pk": record.pk}),
            record.pk,
        )


class LeadingOrderFileUploadActionTable(djt.Table):
    id = djt.LinkColumn("recon:lo_fileupload_update", args=[A("pk")])
    dt_created = djt.DateTimeColumn(format=DT_FORMAT)
    input_col = djt.TemplateColumn(
        verbose_name="input file",
        template_code='<a href="{{record.get_input_url}}">{{record.get_input_name}}</a>',
        orderable=False,
    )

    class Meta:
        model = models.LeadingOrderFileUploadModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = (
            "id",
            "dt_created",
            "name",
            "user_created",
            "status",
            "processing_time",
        )
        per_page = 10

    def render_id(self, value):
        """
        Renders the ID as a shortened string for display.
        'value' is the full MongoDB ID.
        """
        val_str = str(value)
        # Check if the string is long enough to shorten (3 + 3 dots + 5 = 11)
        if len(val_str) > 8:
            return f"{val_str[:3]}...{val_str[-5:]}"
        # Return as-is if it's not the expected length
        return val_str

    def render_processing_time(self, value):
        return render_processing_time(value)


class LeadingOrderTransformTable(djt.Table):
    class Meta:
        model = models.LeadingOrderTransformModel
        template_name = "django_tables2/bootstrap5-responsive.html"

    def render_processing_time(self, value):
        return render_processing_time(value)


class SalesFileUploadActionTable(djt.Table):
    id = djt.LinkColumn("recon:sales_fileupload_update", args=[A("pk")])
    dt_created = djt.DateTimeColumn(format=DT_FORMAT)
    input_col = djt.TemplateColumn(
        verbose_name="input file",
        template_code='<a href="{{record.get_input_url}}">{{record.get_input_name}}</a>',
        orderable=False,
    )

    class Meta:
        model = models.SalesFileUploadModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = (
            "id",
            "dt_created",
            "name",
            "user_created",
            "status",
            "processing_time",
        )
        per_page = 10

    def render_id(self, value):
        """
        Renders the ID as a shortened string for display.
        'value' is the full MongoDB ID.
        """
        val_str = str(value)
        # Check if the string is long enough to shorten (3 + 3 dots + 5 = 11)
        if len(val_str) > 8:
            return f"{val_str[:3]}...{val_str[-5:]}"
        # Return as-is if it's not the expected length
        return val_str

    def render_processing_time(self, value):
        return render_processing_time(value)


class SalesTransformTable(djt.Table):
    class Meta:
        model = models.SalesTransformModel
        template_name = "django_tables2/bootstrap5-responsive.html"

    def render_processing_time(self, value):
        return render_processing_time(value)


class OpsFileUploadActionTable(djt.Table):
    id = djt.LinkColumn("recon:ops_fileupload_update", args=[A("pk")])
    dt_created = djt.DateTimeColumn(format=DT_FORMAT)
    input_col = djt.TemplateColumn(
        verbose_name="input file",
        template_code='<a href="{{record.get_input_url}}">{{record.get_input_name}}</a>',
        orderable=False,
    )

    class Meta:
        model = models.OpsFileUploadModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = (
            "id",
            "dt_created",
            "name",
            "user_created",
            "status",
            "processing_time",
        )
        per_page = 10

    def render_id(self, value):
        """
        Renders the ID as a shortened string for display.
        'value' is the full MongoDB ID.
        """
        val_str = str(value)
        # Check if the string is long enough to shorten (3 + 3 dots + 5 = 11)
        if len(val_str) > 8:
            return f"{val_str[:3]}...{val_str[-5:]}"
        # Return as-is if it's not the expected length
        return val_str

    def render_processing_time(self, value):
        return render_processing_time(value)


class OpsTransformTable(djt.Table):
    class Meta:
        model = models.OpsTransformModel
        template_name = "django_tables2/bootstrap5-responsive.html"

    def render_processing_time(self, value):
        return render_processing_time(value)


class HelloListTable(djt.Table):
    dt_created = djt.DateTimeColumn(format=DT_FORMAT)
    output = djt.TemplateColumn(
        template_code='{% if record.get_output_name == "none" %}{{record.get_output_name}}{% elif record.get_output_name == "ParseExcelError" %}{{record.get_output_name}}{% else %}<a href="{{record.get_output_url}}">{{record.get_output_name}}</a>{% endif %}',
        template_name="output",
        orderable=False,
    )

    class Meta:
        model = models.HelloModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = (
            "id",
            "dt_created",
            "user_created",
            "name",
            "status",
        )

    def render_processing_time(self, value):
        if value > 120:
            minutes = value / 60
            if minutes > 60:
                hours = minutes / 60
                return f"{hours:.3f}hrs"
            return f"{minutes:.3f}mins"
        return f"{value:.3f}s"


class HelloActionTable(djt.Table):
    id = djt.LinkColumn("recon:hello_change", args=[A("pk")])
    dt_created = djt.DateTimeColumn(format=DT_FORMAT)
    input_ = djt.TemplateColumn(
        template_code='<a href="{{record.get_input_url}}">{{record.get_input_name}}</a>',
        template_name="input",
        orderable=False,
    )
    output = djt.TemplateColumn(
        template_code='{% if record.get_output_name == "none" %}{{record.get_output_name}}{% elif record.get_output_name == "ParseExcelError" %}{{record.get_output_name}}{% else %}<a href="{{record.get_output_url}}">{{record.get_output_name}}</a>{% endif %}',
        template_name="output",
        orderable=False,
    )
    delete_action = djt.Column(empty_values=(), orderable=False, verbose_name="Action")

    class Meta:
        model = models.HelloModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = (
            "id",
            "dt_created",
            "name",
            "user_created",
            "status",
            "data",
            "processing_time",
        )

    def render_id(self, value):
        """
        Renders the ID as a shortened string for display.
        'value' is the full MongoDB ID.
        """
        val_str = str(value)
        # Check if the string is long enough to shorten (3 + 3 dots + 5 = 11)
        if len(val_str) > 8:
            return f"{val_str[:3]}...{val_str[-5:]}"
        # Return as-is if it's not the expected length
        return val_str

    def render_processing_time(self, value):
        if value > 120:
            minutes = value / 60
            if minutes > 60:
                hours = minutes / 60
                return f"{hours:.3f}hrs"
            return f"{minutes:.3f}mins"
        return f"{value:.3f}s"

    def render_delete_action(self, record):
        return format_html(
            '<a href="{}" class="btn btn-sm btn-danger">Delete</a>',
            reverse("recon:hello_delete", kwargs={"pk": record.pk}),
            record.pk,
        )
