"""Telegram user model."""

import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now


class TelegramUser(models.Model):
    """Telegram user model."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="telegram_user",
    )
    telegram_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    username = models.CharField(max_length=150, blank=True)

    def __str__(self) -> str:
        """Return string representation."""
        return self.user.username


class AuthToken(models.Model):
    """Model to store authentication tokens."""

    token = models.UUIDField(default=uuid.uuid4, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(default=now)
    expires_at = models.DateTimeField()

    def __str__(self) -> str:
        """Return string representation."""
        return str(self.token)

    def is_valid(self) -> bool:
        """Check if the token is still valid."""
        return now() < self.expires_at
