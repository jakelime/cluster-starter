# creds/validators.py
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.deconstruct import deconstructible


def validate_username_not_reserved(value):
    reserved_names = ["admin", "superuser", "root"]
    if value.lower() in reserved_names:
        raise ValidationError(
            "This username is reserved.",
            code="reserved_username",
        )


def validate_username_unique(value):
    User = get_user_model()
    if User.objects.filter(username=value).exists():
        raise ValidationError(
            "This username is already taken.",
            code="username_taken",
        )


def validate_lowercase(value):
    if value != value.lower():
        raise ValidationError(
            "Username must be lowercase.",
            code="lowercase_required",
        )


@deconstructible
class WhitelistEmailValidator(EmailValidator):
    def validate_domain_part(self, domain_part):
        return False

    def __eq__(self, other):
        return isinstance(other, WhitelistEmailValidator) and super().__eq__(other)
