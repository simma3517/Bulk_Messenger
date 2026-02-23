from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Roles(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        SUPPORT = "SUPPORT", "Support"
        MANAGER = "MANAGER", "Manager"
        USER = "USER", "User"

    role = models.CharField(max_length=20, choices=Roles.choices)

    # hierarchy: manager owns users
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children'
    )

    is_blocked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.role})"