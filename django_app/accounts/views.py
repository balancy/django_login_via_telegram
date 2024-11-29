"""Accounts app views."""

import json
import logging
import uuid
from datetime import timedelta
from http import HTTPStatus
from typing import Any

from common.utils import generate_random_password
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View

from .models import AuthToken, TelegramUser

logger = logging.getLogger(__name__)


class LoginView(TemplateView):
    """Login view."""

    template_name = "accounts/login.html"

    def get_context_data(self, **kwargs: str) -> dict[str, Any]:
        """Get context data."""
        context = super().get_context_data(**kwargs)

        auth_token = AuthToken.objects.create(
            token=uuid.uuid4(),
            expires_at=now() + timedelta(minutes=10),  # Токен истекает через 10 минут
        )
        logger.info("Generated auth token: %s", auth_token.token)
        context["token"] = str(auth_token.token)
        context["telegram_bot_link"] = settings.TELEGRAM_BOT_LINK

        return context


class CheckAuthStatusView(View):
    """Check auth status view."""

    def get(self, request: HttpRequest, *args: str, **kwargs: str) -> JsonResponse:
        """Get auth status."""
        auth_token = request.GET.get("token")

        if not auth_token:
            logger.info("No token provided in browser session.")
            return JsonResponse({"is_authenticated": False, "redirect": None})

        try:
            token_obj = AuthToken.objects.get(token=auth_token, user__isnull=False)
            user = token_obj.user

            logger.info(
                "Token received: %s, Associated user: %s",
                auth_token,
                token_obj.user.username if token_obj else "No user",
            )

            if not request.user.is_authenticated:
                login(request, user)
                logger.info("Browser session synchronized for user: %s", user.username)

            token_obj.delete()
            logger.info("Token %s deleted after successful browser sync.", auth_token)

            return JsonResponse({"is_authenticated": True, "redirect": None})
        except AuthToken.DoesNotExist:
            logger.info("No valid token found for browser session.")
            return JsonResponse({"is_authenticated": False, "redirect": None})


@method_decorator(csrf_exempt, name="dispatch")
class TelegramAuthView(View):
    """Telegram auth view."""

    def post(self, request: HttpRequest, *args: str, **kwargs: str) -> JsonResponse:
        """Telegram auth."""
        logger.info("POST data received: %s", request.body)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid payload"},
                status=400,
            )

        token = data.get("token")
        telegram_id = data.get("telegram_id")
        username = data.get("username")

        if not token or not telegram_id or not username:
            return JsonResponse(
                {"status": "error", "message": "Missing required fields"},
                status=HTTPStatus.BAD_REQUEST,
            )

        first_name = data.get("first_name")
        last_name = data.get("last_name")

        logger.info("Received token: %s", token)

        try:
            auth_token = AuthToken.objects.get(token=token)
            if not auth_token.is_valid():
                return JsonResponse(
                    {"status": "error", "message": "Token expired"},
                    status=HTTPStatus.BAD_REQUEST,
                )
        except AuthToken.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Invalid token"},
                status=HTTPStatus.BAD_REQUEST,
            )

        user = self._get_or_create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        auth_token.user = user
        auth_token.save()

        login(request, user)
        logger.info("User authenticated: %s", user.username)

        return JsonResponse(
            {
                "status": "success",
                "message": "User authenticated successfully!",
            },
        )

    @transaction.atomic
    def _get_or_create_user(
        self,
        telegram_id: int,
        username: str,
        first_name: str,
        last_name: str,
    ) -> User:
        """Retrieve or create a User and TelegramUser.

        If a User with the given username exists but is not associated
        with a TelegramUser, link them.
        """
        try:
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
            logger.info("Found existing TelegramUser for telegram_id: %s", telegram_id)
        except TelegramUser.DoesNotExist:
            logger.info("No TelegramUser found for telegram_id: %s", telegram_id)
        else:
            return telegram_user.user

        try:
            user = User.objects.get(username=username)
            logger.info("Rebinding TelegramUser to existing User: %s", username)
        except User.DoesNotExist:
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
        logger.info("Created and linked TelegramUser for telegram_id: %s", telegram_id)

        return user
