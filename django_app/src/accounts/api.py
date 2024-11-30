"""Accounts app apis."""

import logging
import uuid
from datetime import timedelta
from http import HTTPStatus
from typing import Any

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.timezone import now
from ninja import NinjaAPI
from ninja.errors import HttpError

from accounts.schemas import TelegramAuthSchema
from common.utils import generate_random_password

from .models import AuthToken, TelegramUser

logger = logging.getLogger(__name__)

api = NinjaAPI()

@api.get("/")
def login_view(request: HttpRequest) -> HttpResponse:
    """Login view."""
    auth_token = AuthToken.objects.create(
        token=uuid.uuid4(),
        expires_at=now() + timedelta(minutes=10),
    )
    context = {
        "token": str(auth_token.token),
        "telegram_bot_link": settings.TELEGRAM_BOT_LINK,
    }
    return render(request, "accounts/login.html", context)


@api.get("/check-auth-status/")
def check_auth_status(request: HttpRequest, token: uuid.UUID | None = None) -> dict[str, Any]:
    """Check auth status."""
    if not token:
        logger.info("No token provided in browser session.")
        return {"is_authenticated": False, "redirect": None}

    token_obj = AuthToken.objects.filter(token=token, user__isnull=False).first()
    if not token_obj:
        logger.info("Invalid or expired token.")
        return {"is_authenticated": False, "redirect": None}

    user = token_obj.user
    if not request.user.is_authenticated:
        with transaction.atomic():
            token_obj.delete()
            login(request, user)

    logger.info("Browser session synchronized for user: %s", user.username)

    return {"is_authenticated": True, "redirect": None}


@api.post("/telegram-auth/")
def telegram_auth(request: HttpRequest, payload: TelegramAuthSchema) -> dict[str, str]:
    """Telegram auth."""
    logger.info("Telegram auth request received.")

    auth_token = AuthToken.objects.filter(token=payload.token).first()
    if not auth_token or not auth_token.is_valid():
        raise HttpError(
            HTTPStatus.BAD_REQUEST,
            "Invalid or expired token",
        )

    user = _get_or_create_user(payload)
    auth_token.user = user
    auth_token.save()

    login(request, user)
    logger.info("User authenticated: %s", user.username)

    return {
        "status": "success",
        "message": "User authenticated successfully!",
    }


def _get_or_create_user(payload: TelegramAuthSchema) -> User:
    """Retrieve or create a User and TelegramUser."""
    telegram_id = payload.telegram_id
    username = payload.username
    first_name = payload.first_name
    last_name = payload.last_name

    with transaction.atomic():
        telegram_user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
        if telegram_user:
            logger.info("Found existing TelegramUser for telegram_id: %s", telegram_id)
            return telegram_user.user

        user = User.objects.filter(username=username).first()
        if user:
            logger.info("Rebinding TelegramUser to existing User: %s", username)
        else:
            logger.info("Creating new User with username: %s", username)
            user = User.objects.create_user(
                username=username,
                password=generate_random_password(),
                first_name=first_name,
                last_name=last_name,
            )

        TelegramUser.objects.create(
            user=user,
            telegram_id=telegram_id,
            username=username,
        )
        logger.info(
            "Created and linked TelegramUser for telegram_id: %s",
            telegram_id,
        )

    return user
