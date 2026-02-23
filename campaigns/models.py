from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Campaign(models.Model):

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("PARTIAL", "Partial"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    message = models.TextField()
    total_numbers = models.IntegerField(default=0)
    valid_numbers = models.IntegerField(default=0)
    invalid_numbers = models.IntegerField(default=0)
    duplicate_numbers = models.IntegerField(default=0)
    balance_deducted = models.IntegerField(default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} - {self.name}"
    

class CampaignRecipient(models.Model):

    STATUS = (
        ("PENDING", "Pending"),
        ("SENT", "Sent"),
        ("DELIVERED", "Delivered"),
        ("FAILED", "Failed"),
    )

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="recipients")
    mobile_number = models.CharField(max_length=10)
    api_message_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="PENDING")

    def __str__(self):
        return f"{self.mobile_number} ({self.status})"    