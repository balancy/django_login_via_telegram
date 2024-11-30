"""Delete unused tokens."""

from django.core.management.base import BaseCommand

from accounts.models import AuthToken


class Command(BaseCommand):
    """Delete unused tokens."""

    help = "Delete all AuthToken instances without associated users"

    def handle(self, **_: str) -> None:
        """Handle command."""
        tokens_to_delete = AuthToken.objects.filter(user__isnull=True)

        count = tokens_to_delete.count()
        self.stdout.write(f"Found {count} unused tokens to delete.")

        tokens_to_delete.delete()

        self.stdout.write(f"Deleted {count} unused tokens successfully.")
