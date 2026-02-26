from django.conf import settings
from django.db import models


class Campaign(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    message = models.TextField()
    media = models.FileField(upload_to='campaign_media/', null=True, blank=True)
    total_numbers = models.IntegerField(default=0)
    valid_numbers = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default="PENDING")
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

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="recipients"
    )

    mobile_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS, default="PENDING")

    def __str__(self):
        return f"{self.mobile_number} ({self.status})"