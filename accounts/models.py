from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Roles(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        SUPPORT = "SUPPORT", "Support"
        MANAGER = "MANAGER", "Manager"
        USER = "USER", "User"

    role = models.CharField(max_length=20, choices=Roles.choices,default="USER" )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children'
    )

    is_blocked = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.username} ({self.role})"


# ✅ ADD THIS BELOW User model
class BalanceTransaction(models.Model):

    TRANSACTION_TYPES = (
        ("DEBIT", "Debit"),
        ("CREDIT", "Credit"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"