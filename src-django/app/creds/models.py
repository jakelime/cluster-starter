# creds/models.py
import re
from collections import deque, namedtuple
from logging import getLogger
from typing import Dict, List, Tuple

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy
from django_mongodb_backend import fields

lg = getLogger("django")

ParsedEmailNames = namedtuple("ParsedEmailNames", ["first", "last", "preferred"])


def clean_username(username: str) -> str:
    """
    Cleans a username string based on the following rules:
    - Only allows lowercase letters (a-z), numbers (0-9), dot (.), hyphen (-), and underscore (_).
    - Numbers are NOT allowed as the first character.
    - Converts all characters to lowercase.
    - Condenses multiple consecutive invalid characters (now replaced by '_').
    - Strips leading/trailing allowed separator characters (._-).

    Args:
        username: The raw input string.

    Returns:
        The cleaned, sanitized username string.
    """
    if not isinstance(username, str) or not username:
        return ""

    # 1. Convert to lowercase
    cleaned = username.lower()

    # 2. Replace illegal characters with an underscore.
    # The regex pattern [^a-z0-9._-] matches any character *not* in the allowed set.
    cleaned = re.sub(r"[^a-z0-9._-]", "_", cleaned)

    # 3. Check if the string starts with a number (0-9). If so, prepend an underscore
    # to satisfy the "must not start with a number" rule.
    if cleaned[0].isdigit():
        cleaned = "_" + cleaned

    # 4. Condense multiple consecutive underscores/separators created during cleaning
    # into a single one (e.g., "a__b" -> "a_b")
    cleaned = re.sub(r"[._-]{2,}", "_", cleaned)

    # 5. Remove any leading or trailing separator characters (._-).
    cleaned = cleaned.strip("._-")

    # Final check for empty string after stripping
    if not cleaned:
        # If the string was stripped down to nothing (e.g., '123' -> '_123' -> strip('._-') -> ''),
        # return a sensible default or raise an error, but here we return a placeholder.
        raise ValueError("Username cannot be cleaned.")

    return cleaned


def parse_email_to_names(email_address: str) -> ParsedEmailNames:
    """
    Parses an email address (or the local-part of an email) to extract
    [first_name, last_name, preferred_name] based on common naming conventions
    found in the provided examples.

    Args:
        email_address: The input email string (e.g., "jake.lim@email.com").

    Returns:
        A list [first_name, last_name, preferred_name].
    """

    # 1. Standardize and Extract Local Part
    # Split by '@' and take the first part (the local part), then convert to lowercase
    # This handles both "user@domain.com" and "user.name" formats
    local_part = email_address.split("@")[0].lower()

    # 2. Split Local Part by Common Delimiters
    # Use re.split to split by '.', '_', or '-', keeping only non-empty strings
    # The  tag could be added here to visually illustrate how re.split works on a string like "a.b_c-d" if the concept were less familiar, but for this specific application, the code is clear.
    parts = [p.capitalize() for p in re.split(r"[._-]", local_part) if p]

    # Initialize names
    first_name = ""
    last_name = ""
    preferred_name = ""

    # 3. Assign Names based on the number of parts
    num_parts = len(parts)

    if num_parts == 0:
        # Should not happen if local_part is non-empty, but for completeness
        first_name = local_part
        preferred_name = local_part
        last_name = ""

    elif num_parts == 1:
        # Case: "jakelim@email.com" or "haYjpyCPsBgaQDpz@email.com"
        # Since no separator was found, the whole string is treated as the first/preferred name
        # The first part is the capitalized version from the split.
        first_name = parts[0]
        preferred_name = parts[0]
        last_name = ""

        # Handle the special case where the original local_part was a long string
        # with no delimiters, but the requirement is to return the original string
        # as First/Preferred Name (e.g., "Jakelim" or "Hayjpycpsbgaqdpz").
        # The parts[0] is already the capitalized version of the whole local_part.

    elif num_parts == 2:
        # Case: "jake.lim@email.com" or "daryllpick.cabral"
        first_name = parts[0]
        last_name = parts[1]
        preferred_name = parts[0]

    elif num_parts >= 3:
        # Case: "peckhua.geraldine.ng" or "jeetherkendricramos.mangandi"
        # - The first part is the first name and preferred name.
        # - The remaining parts are joined to form the last name, separated by a space.

        # Use deque for efficient popping from the left
        parts_deque = deque(parts)

        # First part is the first name
        first_name = parts_deque.popleft()
        preferred_name = first_name

        # The rest of the parts form the last name, joined by a space
        last_name = " ".join(parts_deque)

    # 4. Return the result
    return ParsedEmailNames(first_name, last_name, preferred_name)


class UserModel(AbstractUser):
    id = fields.ObjectIdAutoField(primary_key=True)
    first_name = models.CharField(blank=True, max_length=32)
    last_name = models.CharField(blank=True, max_length=32)
    preferred_name = models.CharField(blank=True, max_length=64)
    username = models.CharField(max_length=32, blank=True, null=True, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    is_verified_email = models.BooleanField(default=False)

    class Meta:
        permissions = [
            ("admin_usersmodel", "Can admin users"),
            ("view_sourcecode", "Can view source code"),
        ]

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # Set a default username if not provided
        if not self.username and not self.email:
            self.username = f"user_{UserModel.objects.count() + 1}"
        if self.username:
            self.username = clean_username(self.username)

        # Automatically parse names from email if not provided
        parsed_names = ""
        if not self.preferred_name:
            try:
                parsed_names = parse_email_to_names(self.email)
                self.preferred_name = parsed_names.preferred
                self.first_name = parsed_names.first
                self.last_name = parsed_names.last
            except Exception as e:
                lg.error(f"Error parsing email to names: {e}")
        if not self.first_name:
            if parsed_names:
                self.first_name = parsed_names.first
            else:
                self.first_name = "unnamed"
        if not self.last_name:
            if parsed_names:
                self.last_name = parsed_names.last
            else:
                self.last_name = "user"

        return super().save(*args, **kwargs)

    def get_update_url(self):
        return reverse_lazy("creds:user_update", kwargs={"pk": self.pk})

    def get_profile_url(self):
        return reverse_lazy("creds:user_me", kwargs={"pk": self.pk})

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def activate_user(self):
        self.is_active = True
        self.email_is_verified = True
        self.save()

    def deactivate_user(self):
        self.is_active = False
        self.email_is_verified = False
        self.save()


class DepartmentRoleModel(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=256)

    def __str__(self):
        return f"{self.name}"


class EmployeeModel(models.Model):
    user = models.OneToOneField(
        "creds.UserModel",
        on_delete=models.CASCADE,
        related_name="employee_record",
        null=True,
        blank=True,
    )
    employee_id = models.CharField(unique=True, max_length=32)
    name = models.CharField(max_length=128)

    def __str__(self):
        return f"{self.employee_id}: {self.name}"


class UserModelManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(gettext_lazy("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(gettext_lazy("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(gettext_lazy("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)
