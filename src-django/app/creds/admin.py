# creds/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy

from creds import forms as creds_forms
from creds import models

UserModel = get_user_model()


@admin.register(UserModel)
class UserAdmin(UserAdmin):
    add_form = creds_forms.UserCreationForm
    form = creds_forms.UserChangeForm
    model = UserModel
    list_display = ["username", "email", "date_joined", "preferred_name"]
    fieldsets = (
        (
            gettext_lazy("Security"),
            {
                "fields": (
                    "username",
                    "email",
                    "email_is_verified",
                    "password",
                )
            },
        ),
        (
            gettext_lazy("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "preferred_name",
                )
            },
        ),
        (
            gettext_lazy("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (gettext_lazy("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )


admin.site.register(models.EmployeeModel)
admin.site.register(models.DepartmentRoleModel)
