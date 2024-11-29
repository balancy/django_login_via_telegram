"""Admin settings for models."""

from django.contrib import admin

from accounts.models import AuthToken, TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    """Admin settings for TelegramUser model."""

    list_display = ("user", "telegram_id", "username")
    list_filter = ("user",)
    search_fields = ("user__username",)


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    """Admin settings for AuthToken model."""

    list_display = ("user", "token", "created_at", "expires_at")
    list_filter = ("user",)
    search_fields = ("user__username",)
