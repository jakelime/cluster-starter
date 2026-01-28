# creds/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from creds import views

app_name = "creds"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("me/", views.UserProfileUpdateView.as_view(), name="user_me"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("register/", views.UserRegisterView.as_view(), name="user_register"),
    path(
        "register-status/<str:status>/",
        views.RegisterStatusView.as_view(),
        name="register_status",
    ),
    path(
        "update/<str:pk>/",
        views.UserUpdateView.as_view(),
        name="user_update",
    ),
    path(
        "activate-user/<str:pk>/",
        views.UserActivateView.as_view(),
        name="admin_activate",
    ),
    path(
        "activate/<str:uidb64>/<str:token>/",
        views.activate_view,
        name="user_activate",
    ),
    path(
        "deactivate-user/<str:pk>/",
        views.UserDeactivateView.as_view(),
        name="admin_deactivate",
    ),
    # path("login/", auth_views.LoginView.as_view(), name="login"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path("password_reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
