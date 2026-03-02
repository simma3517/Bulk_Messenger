import csv
import requests

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import F
from django.contrib.auth import get_user_model

from accounts.models import BalanceTransaction
from .models import Campaign, CampaignRecipient
from .validators import clean_numbers
from reports.models import Report

User = get_user_model()


@login_required
def create_campaign(request):

    if request.method != "POST":
        return render(request, "campaigns/create_campaign.html")

    name = request.POST.get("name")
    message = request.POST.get("message")
    numbers_text = request.POST.get("numbers")
    media_file = request.FILES.get("media")

    result = clean_numbers(numbers_text)
    valid_numbers = result.get("valid", [])

    if not valid_numbers:
        return JsonResponse({
            "status": "error",
            "message": "No valid numbers found."
        })

    required_credits = len(valid_numbers)
    success_count = 0
    fail_count = 0

    with transaction.atomic():

        # 🔒 SAFE ATOMIC BALANCE DEDUCTION (NO NEGATIVE BALANCE)
        updated = User.objects.filter(
            id=request.user.id,
            balance__gte=required_credits
        ).update(balance=F('balance') - required_credits)

        if updated == 0:
            return JsonResponse({
                "status": "error",
                "message": "Insufficient balance."
            })

        request.user.refresh_from_db()

        # 📌 Create Campaign
        campaign = Campaign.objects.create(
            user=request.user,
            name=name,
            message=message,
            media=media_file,
            total_numbers=required_credits,
            valid_numbers=required_credits,
            status="PROCESSING"
        )

        # 💳 Log Transaction
        BalanceTransaction.objects.create(
            user=request.user,
            amount=required_credits,
            transaction_type="DEBIT",
            description=f"Campaign {campaign.id} created"
        )

        # 🚀 SEND WHATSAPP MESSAGES
        for number in valid_numbers:

            status_value = "FAILED"

            try:
                if not number.startswith("91"):
                    number = "91" + number

                payload = {
                    "instance_id": settings.WA_INSTANCE_ID,
                    "access_token": settings.WA_ACCESS_TOKEN,
                    "number": number,
                }

                # If Media Exists
                if campaign.media:
                    media_url = request.build_absolute_uri(campaign.media.url)
                    payload.update({
                        "type": "media",
                        "media_url": media_url,
                        "caption": message
                    })
                else:
                    payload.update({
                        "type": "text",
                        "message": message
                    })

                response = requests.post(
                    settings.WA_BASE_URL,
                    data=payload,  # IMPORTANT
                    timeout=20
                )

                print("STATUS:", response.status_code)
                print("RAW RESPONSE:", response.text)

                try:
                    api_response = response.json()
                except Exception:
                    api_response = {}

                # ✅ STRONG SUCCESS CHECK
                if (
                    api_response.get("status") == "success" and
                    api_response.get("message", {}).get("status") == "SUCCESS"
                ):
                    status_value = "DELIVERED"
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                print("ERROR:", str(e))
                fail_count += 1

            CampaignRecipient.objects.create(
                campaign=campaign,
                mobile_number=number,
                status=status_value
            )

        # 📊 Final Campaign Status
        if success_count == required_credits:
            campaign.status = "COMPLETED"
        elif success_count > 0:
            campaign.status = "PARTIAL"
        else:
            campaign.status = "FAILED"

        campaign.save()

    return JsonResponse({
        "status": "success",
        "total": required_credits,
        "delivered": success_count,
        "failed": fail_count,
        "deducted": required_credits,
        "campaign_id": campaign.id
    })

# =====================================
# CAMPAIGN DETAIL
# =====================================

@login_required
def campaign_detail(request, campaign_id):

    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipients = campaign.recipients.all()

    total = recipients.count()
    sent = recipients.filter(status="DELIVERED").count()
    failed = recipients.filter(status="FAILED").count()

    success_rate = 0
    if total > 0:
        success_rate = round((sent / total) * 100, 2)

    if request.method == "POST":
        report_file = request.FILES.get("report_file")

        if report_file:

            Report.objects.create(
                campaign=campaign,
                report_file=report_file
            )

            decoded_file = report_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            for row in reader:
                number = row.get("mobile_number")
                status = row.get("status", "").upper()

                try:
                    recipient = CampaignRecipient.objects.get(
                        campaign=campaign,
                        mobile_number=number
                    )

                    recipient.status = status
                    recipient.save()

                except CampaignRecipient.DoesNotExist:
                    continue

    return render(request, "campaigns/campaign_detail.html", {
        "campaign": campaign,
        "recipients": recipients,
        "total": total,
        "sent": sent,
        "failed": failed,
        "success_rate": success_rate,
    })


@login_required
def download_csv(request, campaign_id):

    campaign = get_object_or_404(Campaign, id=campaign_id)
    recipients = campaign.recipients.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="campaign_{campaign_id}.csv"'

    writer = csv.writer(response)

    # Header row
    writer.writerow([
        "Campaign ID",
        "Campaign Name",
        "Message",
        "Attachment",
        "Mobile Number",
        "Status"
    ])

    # Attachment URL
    attachment_url = ""
    if campaign.media:
        attachment_url = request.build_absolute_uri(campaign.media.url)

    for r in recipients:
        writer.writerow([
            campaign.id,
            campaign.name,
            campaign.message,
            attachment_url,
            r.mobile_number,
            r.status
        ])

    return response


@login_required
def retry_failed(request, campaign_id):

    campaign = get_object_or_404(Campaign, id=campaign_id)
    failed_recipients = campaign.recipients.filter(status="FAILED")

    for recipient in failed_recipients:

        try:
            number = recipient.mobile_number
            if not number.startswith("91"):
                number = "91" + number

            payload = {
                "instance_id": settings.WA_INSTANCE_ID,
                "access_token": settings.WA_ACCESS_TOKEN,
                "number": number,
            }

            if campaign.media:
                media_url = request.build_absolute_uri(campaign.media.url)
                payload.update({
                    "type": "media",
                    "media_url": media_url,
                    "caption": campaign.message
                })
            else:
                payload.update({
                    "type": "text",
                    "message": campaign.message
                })

            response = requests.post(
                settings.WA_BASE_URL,
                json=payload,
                timeout=30
            )

            api_response = response.json()

            if api_response.get("status") == "success":
                recipient.status = "DELIVERED"
                recipient.save()

        except Exception as e:
            print("Retry Error:", e)

    return redirect("campaign_detail", campaign_id=campaign_id)


