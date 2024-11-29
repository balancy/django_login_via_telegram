"""URL configuration for accounts app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.LoginView.as_view(), name="login"),
    path("telegram-auth/", views.TelegramAuthView.as_view(), name="telegram_auth"),
    path(
        "check-auth-status/",
        views.CheckAuthStatusView.as_view(),
        name="check_auth_status",
    ),
]
