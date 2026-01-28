# app/forms.py
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset, Layout, Submit
from django.forms import ModelForm
from django_json_widget.widgets import JSONEditorWidget

# Importing custom field wrappers based on your provided context
from main.forms import CssMFieldLarge

from app import models


class ConfigSettingsUpdateForm(ModelForm):
    helper = FormHelper()
    helper.help_text_inline = True
    layout_elements = [
        Fieldset(
            "Configuration Details",
            Div(CssMFieldLarge("name"), css_class="row gx-5"),
            Div(CssMFieldLarge("config"), css_class="row gx-5"),
            css_class="p-3",
        ),
        Div(
            FormActions(
                Submit(
                    "submit",
                    "Update Configuration",
                    css_class="btn btn-primary btn-block p-2",
                ),
            ),
            css_class="py-2",
        ),
    ]
    helper.layout = Layout(*layout_elements)

    class Meta:
        model = models.ConfigSettingsModel
        fields = ("name", "config")
        widgets = {
            "config": JSONEditorWidget,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make 'name' read-only to prevent breaking code references
        name_field = self.fields.get("name")
        if name_field:
            name_field.disabled = True
            name_field.help_text = "System configuration key (Read-Only)."


class ConfigSettingsDetailForm(ModelForm):
    helper = FormHelper()
    helper.help_text_inline = True
    layout_elements = [
        Fieldset(
            "Configuration Details",
            Div(CssMFieldLarge("name"), css_class="row gx-5"),
            Div(CssMFieldLarge("config"), css_class="row gx-5"),
            css_class="p-3",
        ),
    ]
    helper.layout = Layout(*layout_elements)

    class Meta:
        model = models.ConfigSettingsModel
        fields = ("name", "config")
        widgets = {
            "config": JSONEditorWidget(
                options={
                    "mode": "view",
                    "modes": ["view"],
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name_field = self.fields.get("name")
        if name_field:
            name_field.disabled = True
            name_field.help_text = "System configuration key (Read-Only)."
