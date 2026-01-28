# recon/forms.py
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset, Layout, Submit
from django.forms import ModelForm
from main.forms import (
    CssMFieldLarge,
    CssMFieldMedium,
)

from recon import models


class Zmmr3010ReportCreateForm(ModelForm):
    helper = FormHelper()
    helper.help_text_inline = True
    layout_elements = [
        Fieldset(
            "Upload ZMMR3010 Report",
            Div(CssMFieldMedium("name"), css_class="row gx-5"),
            Div(CssMFieldMedium("input_fpath"), css_class="row gx-5"),
            css_class="mb-3",
        ),
        Div(
            FormActions(
                Submit(
                    "submit",
                    "Submit",
                    css_class="btn btn-primary btn-block p-2",
                ),
            ),
            css_class="py-2",
        ),
    ]
    helper.layout = Layout(*layout_elements)

    class Meta:
        model = models.Zmmr3010ReportModel
        fields = ("name", "input_fpath")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = self.fields.get("name")
        if name:
            name.help_text = "Give a unique name per day"


class Zmmr3010ReportUpdateForm(ModelForm):
    helper = FormHelper()
    helper.help_text_inline = True
    layout_elements = [
        Fieldset(
            "Update Attributes",
            Div(CssMFieldLarge("name"), css_class="row gx-5"),
            css_class="p-3",
        ),
        Div(
            FormActions(
                Submit(
                    "submit",
                    "Submit",
                    css_class="btn btn-primary btn-block p-2",
                ),
            ),
            css_class="py-2",
        ),
    ]
    helper.layout = Layout(*layout_elements)

    class Meta:
        model = models.Zmmr3010ReportModel
        fields = ("name", "input_fpath")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = self.fields.get("name")
        if name:
            name.help_text = "Give a unique name."


class LeadingOrderFileUploadCreateForm(ModelForm):
    helper = FormHelper()
    helper.help_text_inline = True
    layout_elements = [
        Fieldset(
            "Sync using LeadingOrder file upload",
            Div(CssMFieldMedium("name"), css_class="row gx-5"),
            Div(CssMFieldMedium("input_fpath"), css_class="row gx-5"),
            css_class="mb-3",
        ),
        Div(
            FormActions(
                Submit(
                    "submit",
                    "Submit",
                    css_class="btn btn-primary btn-block p-2",
                ),
            ),
            css_class="py-2",
        ),
    ]
    helper.layout = Layout(*layout_elements)

    class Meta:
        model = models.LeadingOrderFileUploadModel
        fields = ("name", "input_fpath")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = self.fields.get("name")
        if name:
            name.help_text = "Give a unique name."
        input_fpath = self.fields.get("input_fpath")
        if input_fpath:
            input_fpath.help_text = "Accepts *.json or *.json.gz."


class LeadingOrderFileUploadUpdateForm(ModelForm):
    helper = FormHelper()
    helper.help_text_inline = True
    layout_elements = [
        Fieldset(
            "Update Attributes",
            Div(CssMFieldLarge("name"), css_class="row gx-5"),
            css_class="p-3",
        ),
        Div(
            FormActions(
                Submit(
                    "submit",
                    "Submit",
                    css_class="btn btn-primary btn-block p-2",
                ),
            ),
            css_class="py-2",
        ),
    ]
    helper.layout = Layout(*layout_elements)

    class Meta:
        model = models.LeadingOrderFileUploadModel
        fields = ("name", "input_fpath")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = self.fields.get("name")
        if name:
            name.help_text = "Give a unique name."
        input_fpath = self.fields.get("input_fpath")
        if input_fpath:
            input_fpath.help_text = "Accepts JSON or json.gz files."


class SalesFileUploadCreateForm(ModelForm):
    helper = FormHelper()
    helper.help_text_inline = True
    layout_elements = [
        Fieldset(
            "Sync using Sales file upload",
            Div(CssMFieldMedium("name"), css_class="row gx-5"),
            Div(CssMFieldMedium("input_fpath"), css_class="row gx-5"),
            css_class="mb-3",
        ),
        Div(
            FormActions(
                Submit(
                    "submit",
                    "Submit",
                    css_class="btn btn-primary btn-block p-2",
                ),
            ),
            css_class="py-2",
        ),
    ]
    helper.layout = Layout(*layout_elements)

    class Meta:
        model = models.SalesFileUploadModel
        fields = ("name", "input_fpath")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = self.fields.get("name")
        if name:
            name.help_text = "Give a unique name."
        input_fpath = self.fields.get("input_fpath")
        if input_fpath:
            input_fpath.help_text = "Accepts *.xlsx or *.xlsm."


class SalesFileUploadUpdateForm(ModelForm):
    helper = FormHelper()
    helper.help_text_inline = True
    layout_elements = [
        Fieldset(
            "Update Details",
            Div(CssMFieldLarge("name"), css_class="row gx-5"),
            css_class="p-3",
        ),
        Fieldset(
            "Details (Read-Only)",
            Div(CssMFieldLarge("input_fpath"), css_class="row gx-5"),
            Div(CssMFieldLarge("processing_time"), css_class="row gx-5"),
            Div(CssMFieldLarge("user_created"), css_class="row gx-5"),
            css_class="p-3",
        ),
        Fieldset(
            "Task Run (Read-Only)",
            Div(CssMFieldLarge("task_id"), css_class="row gx-5"),
            Div(CssMFieldLarge("result"), css_class="row gx-5"),
            Div(CssMFieldLarge("traceback"), css_class="row gx-5"),
            Div(CssMFieldLarge("dt_start"), css_class="row gx-5"),
            Div(CssMFieldLarge("dt_end"), css_class="row gx-5"),
            css_class="p-3",
        ),
        Div(
            FormActions(
                Submit(
                    "submit",
                    "Submit",
                    css_class="btn btn-primary btn-block p-2",
                ),
            ),
            css_class="py-2",
        ),
    ]
    helper.layout = Layout(*layout_elements)

    class Meta:
        model = models.SalesFileUploadModel
        fields = (
            "name",
            "input_fpath",
            "processing_time",
            "user_created",
            "task_id",
            "result",
            "traceback",
            "dt_start",
            "dt_end",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = self.fields.get("name")
        if name:
            name.help_text = "Give a unique name."
        self.change_to_readonly_field(
            "input_fpath",
            "processing_time",
            "user_created",
            "task_id",
            "result",
            "traceback",
            "dt_start",
            "dt_end",
        )

    def change_to_readonly_field(self, *args):
        for name in args:
            _field = self.fields.get(name)
            if _field:
                _field.disabled = True


class OpsFileUploadCreateForm(ModelForm):
    helper = FormHelper()
    helper.help_text_inline = True
    layout_elements = [
        Fieldset(
            "Sync using Ops file upload",
            Div(CssMFieldMedium("name"), css_class="row gx-5"),
            Div(CssMFieldMedium("input_fpath"), css_class="row gx-5"),
            css_class="mb-3",
        ),
        Div(
            FormActions(
                Submit(
                    "submit",
                    "Submit",
                    css_class="btn btn-primary btn-block p-2",
                ),
            ),
            css_class="py-2",
        ),
    ]
    helper.layout = Layout(*layout_elements)

    class Meta:
        model = models.OpsFileUploadModel
        fields = ("name", "input_fpath")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = self.fields.get("name")
        if name:
            name.help_text = "Give a unique name."
        input_fpath = self.fields.get("input_fpath")
        if input_fpath:
            input_fpath.help_text = "Accepts *.xlsx or *.xlsm."


class OpsFileUploadUpdateForm(ModelForm):
    helper = FormHelper()
    helper.help_text_inline = True
    layout_elements = [
        Fieldset(
            "Update Details",
            Div(CssMFieldLarge("name"), css_class="row gx-5"),
            css_class="p-3",
        ),
        Fieldset(
            "Details (Read-Only)",
            Div(CssMFieldLarge("input_fpath"), css_class="row gx-5"),
            Div(CssMFieldLarge("processing_time"), css_class="row gx-5"),
            Div(CssMFieldLarge("user_created"), css_class="row gx-5"),
            css_class="p-3",
        ),
        Fieldset(
            "Task Run (Read-Only)",
            Div(CssMFieldLarge("task_id"), css_class="row gx-5"),
            Div(CssMFieldLarge("result"), css_class="row gx-5"),
            Div(CssMFieldLarge("traceback"), css_class="row gx-5"),
            Div(CssMFieldLarge("dt_start"), css_class="row gx-5"),
            Div(CssMFieldLarge("dt_end"), css_class="row gx-5"),
            css_class="p-3",
        ),
        Div(
            FormActions(
                Submit(
                    "submit",
                    "Submit",
                    css_class="btn btn-primary btn-block p-2",
                ),
            ),
            css_class="py-2",
        ),
    ]
    helper.layout = Layout(*layout_elements)

    class Meta:
        model = models.OpsFileUploadModel
        fields = (
            "name",
            "input_fpath",
            "processing_time",
            "user_created",
            "task_id",
            "result",
            "traceback",
            "dt_start",
            "dt_end",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = self.fields.get("name")
        if name:
            name.help_text = "Give a unique name."
        self.change_to_readonly_field(
            "input_fpath",
            "processing_time",
            "user_created",
            "task_id",
            "result",
            "traceback",
            "dt_start",
            "dt_end",
        )

    def change_to_readonly_field(self, *args):
        for name in args:
            _field = self.fields.get(name)
            if _field:
                _field.disabled = True
