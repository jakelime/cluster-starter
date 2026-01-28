# creds/forms.py
from crispy_bootstrap5.bootstrap5 import Field
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Submit
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)
from django.core import validators

from creds import validators as creds_validators

UserModel = get_user_model()


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        required=True,
        label="Username or Email",
    )
    helper = FormHelper()
    helper.layout = Layout(
        Field("username"),
        Field("password"),
        FormActions(
            Submit("submit", "Login", css_class="btn-primary "),
        ),
    )


class UserCreationForm(UserCreationForm):
    # AuthenticationForm inherits from forms.ModelForm,
    # high level and allows crispy form
    username = forms.CharField(
        required=True,
        label="Username",
        help_text="Example: john.doe. Lowercase letters, digits and _ only.",
        validators=[
            validators.RegexValidator(
                regex=r"^[a-z0-9_.]+$",
                message="Lowercase letters, digits and _ only! e.g. john.doe",
                code="invalid_username",
            ),
            validators.MinLengthValidator(
                4, "Username must be at least 4 characters long."
            ),
            creds_validators.validate_username_not_reserved,
            creds_validators.validate_username_unique,
        ],
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        help_text=f"Example: john.doe@{settings.ALLOWED_EMAIL_DOMAINS[0]}",
        validators=[
            validators.EmailValidator(
                allowlist=settings.ALLOWED_EMAIL_DOMAINS,
                message=f"Enter a valid email address; e.g. john.doe@{settings.ALLOWED_EMAIL_DOMAINS[0]}",
            ),
        ],
    )
    helper = FormHelper()
    helper.layout = Layout(
        Field("username"),
        Field("email"),
        Field("password1"),
        Field("password2"),
        FormActions(
            Submit("submit", "Register as new user", css_class="btn-primary "),
        ),
    )

    class Meta:
        model = UserModel
        fields = ("username", "email", "password1", "password2")


class UserChangeForm(UserChangeForm):
    helper = FormHelper()
    helper.layout = Layout(
        Field("email"),
        Field("username"),
        Field(
            "first_name",
        ),
        Field("last_name"),
        Field(
            "preferred_name",
        ),
        Field("groups"),
        Field("is_active"),
        FormActions(
            Submit("submit", "Save", css_class="btn-primary "),
        ),
    )

    class Meta:
        model = UserModel
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "last_name",
            "preferred_name",
            "groups",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        username = self.fields.get("username")
        if username:
            username.disabled = True
        email_is_verified = self.fields.get("email_is_verified")
        if email_is_verified:
            email_is_verified.disabled = True
        email = self.fields.get("email")
        if email:
            email.help_text = "Email id must be same as username!"


class UserProfileForm(UserChangeForm):
    helper = FormHelper()
    helper.layout = Layout(
        Field("email"),
        Field("username"),
        Field("preferred_name"),
        Field("first_name"),
        Field("last_name"),
        FormActions(
            Submit("submit", "Save", css_class="btn-primary "),
        ),
    )

    class Meta:
        model = UserModel
        fields = ("email", "username", "preferred_name", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        username = self.fields.get("username")
        if username:
            username.disabled = True
