



from django.db import models
from campaigns.models import Campaign
is_processed = models.BooleanField(default=False)
class Report(models.Model):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="reports"
    )
    report_file = models.FileField(upload_to="campaign_reports/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False) 

    def __str__(self):
        return f"Report {self.id} - Campaign {self.campaign.id}"