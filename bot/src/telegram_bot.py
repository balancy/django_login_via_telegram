"""Main bot app."""

import os
from http import HTTPStatus

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from logger import logger

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL")

HEADERS = {"Host": "127.0.0.1"}


def main() -> None:
    """Run bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    logger.info("Running bot...")
    application.run_polling()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
    args = context.args
    if not args:
        await _send_message(update, "Auth token not found. Try again.")
        return

    token = args[0]
    telegram_user = _extract_telegram_user(update)
    if not telegram_user:
        await _send_message(
            update,
            "Unable to retrieve your Telegram user. Please try again.",
        )
        return

    data = _construct_data(token, telegram_user)
    await _send_authentication_request(update, data)


async def _send_message(update: Update, text: str) -> None:
    """Send a message to the user."""
    if update.message:
        await update.message.reply_text(text)


def _extract_telegram_user(update: Update) -> dict | None:
    """Extract and validate the Telegram user."""
    telegram_user = update.effective_user
    if not telegram_user:
        return None

    return {
        "id": telegram_user.id,
        "username": telegram_user.username or "",
        "first_name": telegram_user.first_name or "",
        "last_name": telegram_user.last_name or "",
    }


def _construct_data(token: str, telegram_user: dict) -> dict:
    """Construct the data payload for the authentication request."""
    return {
        "token": token,
        "telegram_id": str(telegram_user["id"]),
        "username": telegram_user["username"],
        "first_name": telegram_user["first_name"],
        "last_name": telegram_user["last_name"],
    }


async def _send_authentication_request(update: Update, data: dict) -> None:
    """Send the authentication request to the backend server."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                BACKEND_SERVER_URL,
                json=data,
                headers=HEADERS,
            )
    except httpx.RequestError as e:
        await _send_message(
            update,
            "A connection error occurred. Please try again.",
        )
        logger.info("Error while sending data to backend: %s", e)
    else:
        await _handle_response(update, response)


async def _handle_response(update: Update, response: httpx.Response) -> None:
    """Handle the HTTP response."""
    match response.status_code:
        case HTTPStatus.OK:
            await _send_message(update, "You are successfully authenticated!")
        case HTTPStatus.BAD_REQUEST:
            await _send_message(update, "Invalid token. Please try again.")
        case _:
            await _send_message(
                update,
                "Unexpected error occurred. Try again later.",
            )


if __name__ == "__main__":
    main()
