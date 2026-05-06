from django.contrib.auth.models import AbstractUser
from django.db import models


def avatar_upload_path(instance, filename):
    return f"avatars/user_{instance.pk or 'new'}/{filename}"


class User(AbstractUser):
    """Custom user with role + lightweight profile fields baked in."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)

    avatar = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True)
    bio = models.TextField(blank=True)
    position = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def initials(self) -> str:
        first = (self.first_name or self.username or "?")[:1]
        last = (self.last_name or "")[:1]
        return (first + last).upper() or "U"

    @property
    def display_name(self) -> str:
        full = self.get_full_name()
        return full or self.username

    def __str__(self):
        return self.username
