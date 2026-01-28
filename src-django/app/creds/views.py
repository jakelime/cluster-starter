# creds/views.py
import logging
import smtplib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import CreateView, UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from creds import appfilters
from creds import forms as creds_forms
from creds import tables as creds_tables
from creds.tokens import account_activation_token

lg = logging.getLogger("django")


UserModel = get_user_model()


def activate_view(request, uidb64: str, token: str):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = UserModel.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.email_is_verified = True
        user.save()
        return render(
            request,
            template_name="creds/activation-success.html",
            context={"user": user},
        )
    else:
        return render(request, "creds/activation-invalid.html")


def get_user_profile_view(request):
    return redirect(request.user.get_profile_url())


def home_view(request):
    return redirect(reverse("creds:user_list"))


def hx_user_list_table(request):
    # if not request.htmx:
    #     return HttpResponseForbidden("This endpoint only accepts HTMX requests.")
    table = creds_tables.UserListTable(
        UserModel.objects.all().exclude(username="admin").order_by("-date_joined")
    )
    return render(
        request,
        "creds/partials/user_list_table.html",
        {"table": table},
    )


class UserRegisterView(CreateView):
    form_class = creds_forms.UserCreationForm
    success_url = reverse_lazy("creds:register_status", kwargs={"status": "success"})
    template_name = "creds/auth-register.html"

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        try:
            self.send_email(user, form)
        except smtplib.SMTPRecipientsRefused as e:
            return render(
                self.request,
                template_name="creds/registration-confirm.html",
                context={
                    "msg": f"SMTPRecipientsRefused error, {e=}",
                    "error_msg": "Error occured when trying to send email. Please contact admin to activate your account.",
                },
            )
        except TimeoutError as te:
            return render(
                self.request,
                template_name="creds/registration-confirm.html",
                context={
                    "msg": f"{te}",
                    "error_msg": f"Timeout error occured when trying to send email. Please contact admin to activate your account. Timeout={settings.EMAIL_TIMEOUT}s.",
                },
            )
        except Exception as e:
            return render(
                self.request,
                template_name="creds/registration-confirm.html",
                context={
                    "msg": f"{e}",
                    "error_msg": "Uncaught error occured when trying to send email. Please contact admin to activate your account..",
                },
            )
        return super().form_valid(form)

    def send_email(self, user, form):
        mail_subject = "[ppcs] Activation link for new PPCS account"
        message = render_to_string(
            "creds/activation-email.txt",
            {
                "user": user,
                "domain": self.request.get_host(),
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": account_activation_token.make_token(user),
            },
        )
        to_email = form.cleaned_data.get("email")
        email = EmailMessage(mail_subject, message, to=[to_email])
        email.send(fail_silently=settings.EMAIL_FAIL_SILENTLY)


class UserLoginView(auth_views.LoginView):
    authentication_form = creds_forms.UserLoginForm
    template_name = "creds/auth-login.html"


class UserListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    model = UserModel
    table_class = creds_tables.UserListTable
    template_name = "creds/user-list.html"
    context_object_name = "objects"
    filterset_class = appfilters.UserFilter
    permission_required = ["creds.view_usermodel"]

    def get_queryset(self):
        queryset = (
            self.model.objects.all().exclude(username="admin").order_by("-date_joined")
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Manage Users"
        return context


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = UserModel
    template_name = "creds/user-update.html"
    form_class = creds_forms.UserChangeForm
    context_object_name = "objects"
    success_url = reverse_lazy("creds:user_list")
    permission_required = ["creds.change_usermodel"]

    def has_permission(self):
        """Check if the user has permission to update the profile.
        Allows users to update their own profile, or if user has the
        permission specified in `permission_required`.
        """
        has_perm = super().has_permission()
        is_own_profile = self.get_object().pk == self.request.user.pk
        return has_perm or is_own_profile

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["page_title"] = "Manage: Update User"
        return context


class UserActivateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Handles user account activation via a POST request by an administrator.
    It takes a primary key (pk) in the URL to identify the user.
    """

    model = UserModel
    permission_required = ["creds.admin"]

    def post(self, *args, **kwargs):
        if pk := kwargs.get("pk", None):
            obj = get_object_or_404(self.model, pk=pk)
            obj.activate_user()
            messages.success(
                self.request, f"User ({pk}, {obj.username}) activated successfully."
            )
        return redirect(reverse("creds:user_list"))


class UserDeactivateView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """
    Handles user account activation via a POST request by an administrator.
    It takes a primary key (pk) in the URL to identify the user.
    """

    model = UserModel
    permission_required = ["creds.admin"]

    def post(self, *args, **kwargs):
        if pk := kwargs.get("pk", None):
            obj = get_object_or_404(self.model, pk=pk)
            obj.deactivate_user()
            messages.success(
                self.request, f"User ({pk}, {obj.username}) deactivated successfully."
            )
        return redirect(reverse("creds:user_list"))


class RegisterStatusView(TemplateView):
    template_name = "creds/registration-confirm.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.kwargs.get("status", "unknown")
        if status == "success":
            context["msg"] = "Sign up successful!"
            context["error_msg"] = "Activation link has been sent to your email."

        else:
            context["msg"] = f"{status} error"
        return context


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserModel
    template_name = "creds/user-me.html"
    form_class = creds_forms.UserProfileForm
    success_url = reverse_lazy("creds:user_me")

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"User Profile: {(self.request.user.username)}"
        return context


class PasswordResetView(auth_views.PasswordResetView):
    success_url = reverse_lazy("creds:password_reset_done")
