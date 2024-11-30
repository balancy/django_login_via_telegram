"""Accounts schemas."""


from ninja import Schema


class TelegramAuthSchema(Schema):
    """Telegram auth schema."""

    token: str
    telegram_id: str
    username: str
    first_name: str = ""
    last_name: str = ""
