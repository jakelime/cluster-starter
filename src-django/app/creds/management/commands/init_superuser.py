# yourapp/management/commands/init_superuser.py
import base64
import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Create initial superuser from environment variables (idempotent)."

    def handle(self, *args, **options):
        User = get_user_model()

        username = settings.DJANGO_SUPERUSER_ADMIN
        email = settings.DJANGO_SUPERUSER_EMAIL
        password = os.getenv(
            "DJANGO_SUPERUSER_PASSWORD",
            base64.urlsafe_b64encode(secrets.token_bytes(15)).decode("utf-8"),
        )
        force_update = os.getenv("DJANGO_SUPERUSER_FORCE_UPDATE", "false").lower() in {
            "1",
            "true",
            "yes",
        }

        username_field = getattr(User, "USERNAME_FIELD", "username")
        lookup = {username_field: username}

        try:
            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    **lookup,
                    defaults={
                        # Not all user models have 'email' unique/required; defaults are safe here.
                        "email": email,
                        "is_staff": True,
                        "is_superuser": True,
                    },
                )

                if created:
                    user.set_password(password)
                    user.save(update_fields=["password"])
                    self.stdout.write(
                        self.style.SUCCESS(f"Superuser '{username}' created.")
                    )
                else:
                    msg = f"Superuser '{username}' already exists."
                    if force_update:
                        user.is_staff = True
                        user.is_superuser = True
                        if email:
                            user.email = email
                        user.set_password(password)
                        user.save()
                        msg += " (updated flags/email/password)"
                    self.stdout.write(self.style.SUCCESS(msg))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Error creating/updating superuser: {e}")
            )
            raise
