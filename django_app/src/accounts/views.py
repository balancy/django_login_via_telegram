"""Accounts app views."""

import json
import logging
import uuid
from datetime import timedelta
from http import HTTPStatus
from typing import Any

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View

from common.utils import generate_random_password

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
            expires_at=now() + timedelta(minutes=10),
        )
        context["token"] = str(auth_token.token)
        context["telegram_bot_link"] = settings.TELEGRAM_BOT_LINK

        return context


class CheckAuthStatusView(View):
    """Check auth status view."""

    def get(self, request: HttpRequest) -> JsonResponse:
        """Get auth status."""
        auth_token = request.GET.get("token")

        if not auth_token:
            logger.info("No token provided in browser session.")
            return JsonResponse({"is_authenticated": False, "redirect": None})

        token_obj = self._get_valid_token(auth_token)
        if not token_obj:
            logger.info("Invalid or expired token.")
            return JsonResponse({"is_authenticated": False, "redirect": None})

        user = token_obj.user
        if not request.user.is_authenticated:
            with transaction.atomic():
                token_obj.delete()
                login(request, user)

        logger.info("Browser session synchronized for user: %s", user.username)

        return JsonResponse({"is_authenticated": True, "redirect": None})

    def _get_valid_token(self, auth_token: str) -> AuthToken | None:
        """Fetch a valid token if exists."""
        try:
            return AuthToken.objects.get(token=auth_token, user__isnull=False)
        except AuthToken.DoesNotExist:
            return None


@method_decorator(csrf_exempt, name="dispatch")
class TelegramAuthView(View):
    """Telegram auth view."""

    def post(self, request: HttpRequest) -> JsonResponse:
        """Telegram auth."""
        logger.info("Telegram auth request received.")

        data = self._parse_request_data(request)
        if not data:
            return JsonResponse(
                {"status": "error", "message": "Invalid payload"},
                status=HTTPStatus.BAD_REQUEST,
            )

        if not self._validate_required_fields(data):
            return JsonResponse(
                {"status": "error", "message": "Missing required fields"},
                status=HTTPStatus.BAD_REQUEST,
            )

        auth_token = self._validate_auth_token(data.get("token"))
        if not auth_token:
            return JsonResponse(
                {"status": "error", "message": "Invalid or expired token"},
                status=HTTPStatus.BAD_REQUEST,
            )

        user = self._get_or_create_user(data)
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

    def _parse_request_data(self, request: HttpRequest) -> dict | None:
        """Parse and validate request data."""
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None

    def _validate_required_fields(self, data: dict) -> bool:
        """Check if required fields are present."""
        return all(data.get(field) for field in ("token", "telegram_id", "username"))

    def _validate_auth_token(self, token: str) -> AuthToken | None:
        """Validate the token."""
        try:
            auth_token = AuthToken.objects.get(token=token)
            if auth_token.is_valid():
                return auth_token
        except AuthToken.DoesNotExist:
            return None

    @transaction.atomic
    def _get_or_create_user(self, data: dict) -> User:
        """Retrieve or create a User and TelegramUser.

        If a User with the given username exists but is not associated
        with a TelegramUser, link them.
        """
        telegram_id = data["telegram_id"]
        username = data["username"]
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")

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
