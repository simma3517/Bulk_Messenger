from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from campaigns.models import Campaign, CampaignRecipient
from .models import Report
from accounts.models import BalanceTransaction
from accounts.views import role_required
import csv


# =========================
# REPORTS PAGE (User / Manager / Admin)
# =========================
@login_required
def reports_page(request):

    if request.user.role == "USER":
        base_queryset = Campaign.objects.filter(user=request.user)

    elif request.user.role == "MANAGER":
        base_queryset = Campaign.objects.filter(user__parent=request.user)

    else:
        base_queryset = Campaign.objects.all()

    campaigns = base_queryset.annotate(
        total_count=Count("recipients"),
        delivered_count=Count(
            "recipients",
            filter=Q(recipients__status="DELIVERED")
        ),
        failed_count=Count(
            "recipients",
            filter=Q(recipients__status="FAILED")
        )
    ).order_by("-id")

    return render(request, "reports/reports_page.html", {
        "campaigns": campaigns
    })


# =========================
# SUPPORT PANEL
# =========================
@login_required
@role_required("SUPPORT")
def support_panel(request):
    campaigns = Campaign.objects.all().order_by("-id")

    return render(request, "reports/support_panel.html", {
        "campaigns": campaigns
    })


# =========================
# UPLOAD REPORT + AUTO REFUND
# =========================
@login_required
@role_required("SUPPORT")
def upload_report(request, campaign_id):

    campaign = get_object_or_404(Campaign, id=campaign_id)

    if request.method == "POST":
        report_file = request.FILES.get("report_file")

        if not report_file:
            return redirect("support_panel")

        decoded_file = report_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded_file)

        with transaction.atomic():

            Report.objects.create(
                campaign=campaign,
                report_file=report_file
            )

            for row in reader:
                number = row.get("mobile_number")
                new_status = row.get("status", "").upper()

                try:
                    recipient = CampaignRecipient.objects.get(
                        campaign=campaign,
                        mobile_number=number
                    )

                    old_status = recipient.status

                    if old_status != new_status:

                        recipient.status = new_status
                        recipient.save()

                        # Refund if changed to FAILED
                        if new_status == "FAILED" and old_status != "FAILED":

                            campaign.user.balance += 1
                            campaign.user.save()

                            BalanceTransaction.objects.create(
                                user=campaign.user,
                                amount=1,
                                transaction_type="CREDIT",
                                description=f"Refund for failed number {number}"
                            )

                except CampaignRecipient.DoesNotExist:
                    continue

            # Recalculate campaign status
            total = campaign.recipients.count()
            delivered = campaign.recipients.filter(status="DELIVERED").count()

            if delivered == total:
                campaign.status = "COMPLETED"
            elif delivered > 0:
                campaign.status = "PARTIAL"
            else:
                campaign.status = "FAILED"

            campaign.save()

    return redirect("support_panel")