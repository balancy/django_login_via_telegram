"""Main bot app."""

import os
from http import HTTPStatus

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
    args = context.args

    if not args:
        await update.message.reply_text("Auth token not found. Try again.")
        return

    token = args[0]
    telegram_user = update.effective_user

    if not telegram_user:
        await update.message.reply_text(
            "Unable to retrieve your Telegram user. Please try again.",
        )
        return

    data = {
        "token": token,
        "telegram_id": telegram_user.id,
        "username": telegram_user.username or "",
        "first_name": telegram_user.first_name or "",
        "last_name": telegram_user.last_name or "",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(BACKEND_SERVER_URL, json=data)
            if response.status_code == HTTPStatus.OK:
                await update.message.reply_text("You are successfully authenticated!")
            elif response.status_code == HTTPStatus.BAD_REQUEST:
                await update.message.reply_text("Invalid token. Please try again.")
            else:
                await update.message.reply_text(
                    "Unexpected error occurred. Try again later.",
                )
    except httpx.RequestError as e:
        await update.message.reply_text(
            "A connection error occurred. Please try again.",
        )
        print(f"Error while sending data to Django: {e}")


def main() -> None:
    """Run bot."""
    application: Application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    print("Running bot...")
    application.run_polling()


if __name__ == "__main__":
    main()
