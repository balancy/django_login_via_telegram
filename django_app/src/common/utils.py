"""Utils module."""

import secrets
import string

DEFAULT_LENGTH = 12


def generate_random_password(length: int = DEFAULT_LENGTH) -> str:
    """Generate random password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(characters) for _ in range(length))
