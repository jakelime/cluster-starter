# creds/tables.py
import django_tables2 as djt
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.html import format_html

UserModel = get_user_model()


class UserListTable(djt.Table):
    username = djt.Column(linkify=lambda record: record.get_update_url())
    action = djt.Column(
        empty_values=(),
        verbose_name="Action",
        orderable=False,
    )

    class Meta:
        model = UserModel
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = (
            "username",
            "email",
            "preferred_name",
            "date_joined",
            "last_login",
        )

    def paginate(self, paginator_class=Paginator, per_page=10, page=1, *args, **kwargs):
        per_page = per_page or self._meta.per_page
        self.paginator = paginator_class(self.rows, per_page, *args, **kwargs)
        self.page = self.paginator.page(page)
        return self

    def render_action(self, record):
        if not record.is_active:
            activate_account_url = reverse(
                "creds:admin_activate", kwargs={"pk": record.pk}
            )
            return format_html(
                """
                    <button type="button" 
                            data-username="{}" 
                            data-activate-url="{}"
                            onclick="activateUser(this)" 
                            class="btn btn-sm btn-outline-secondary fw-bold">
                        ACTIVATE
                    </button>
                    """,
                record.username,
                activate_account_url,
            )
        else:
            return format_html('<span class="badge bg-success">Active</span>')
