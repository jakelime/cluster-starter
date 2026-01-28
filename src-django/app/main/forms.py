from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import (
    Div,
    Fieldset,
    Layout,
    Submit,
)


class CssMFieldSmall(Div):
    css_class = "col-sm-12 col-md-6 col-lg-4"


class CssMFieldSM(Div):
    css_class = "col-md-4"


class CssMFieldMedium(Div):
    css_class = "col-md-12 col-lg-6"


class CssMFieldLarge(Div):
    css_class = "col-md-12"


class CssTextBox(Div):
    pass


generic_helper_layout = []
