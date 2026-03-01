import requests
import csv
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse

from .models import Campaign, CampaignRecipient
from .validators import clean_numbers


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction
import requests

from accounts.models import BalanceTransaction
from .models import Campaign, CampaignRecipient



from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.db import transaction
import requests

from accounts.models import BalanceTransaction
from .models import Campaign, CampaignRecipient


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.db import transaction
import requests

from accounts.models import BalanceTransaction
from .models import Campaign, CampaignRecipient
from .validators import clean_numbers


import requests
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction

from accounts.models import BalanceTransaction
from .models import Campaign, CampaignRecipient
from .validators import clean_numbers


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

    print("VALID NUMBERS:", valid_numbers)

    if not valid_numbers:
        return JsonResponse({
            "status": "error",
            "message": "No valid numbers found."
        })

    required_credits = len(valid_numbers)

    if request.user.balance < required_credits:
        return JsonResponse({
            "status": "error",
            "message": "Insufficient balance."
        })

    success_count = 0
    fail_count = 0

    with transaction.atomic():

        # Deduct credits
        request.user.balance -= required_credits
        request.user.save()

        campaign = Campaign.objects.create(
            user=request.user,
            name=name,
            message=message,
            media=media_file,
            total_numbers=required_credits,
            valid_numbers=required_credits,
            status="PROCESSING"
        )

        BalanceTransaction.objects.create(
            user=request.user,
            amount=required_credits,
            transaction_type="DEBIT",
            description=f"Campaign {campaign.id} created"
        )

        # 🔥 SEND MESSAGES (USE POST)
        for number in valid_numbers:

            print("Sending to:", number)
            status_value = "FAILED"

            try:
                response = requests.post(
                    f"{settings.WA_BASE_URL}/http-tokenkeyapi.php",
                    data={
                        "authentic-key": settings.WA_API_KEY,
                        "route": 1,
                        "number": number,
                        "message": message
                    },
                    timeout=30
                )

                print("STATUS CODE:", response.status_code)
                print("RAW RESPONSE:", response.text)

                try:
                    api_response = response.json()
                except Exception:
                    print("⚠ JSON PARSE ERROR")
                    api_response = {}

                print("PARSED RESPONSE:", api_response)

                if api_response.get("Status") == "Success":
                    status_value = "DELIVERED"
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                print("REQUEST ERROR:", str(e))
                fail_count += 1

            CampaignRecipient.objects.create(
                campaign=campaign,
                mobile_number=number,
                status=status_value
            )

        # Refund failed
        if fail_count > 0:
            request.user.balance += fail_count
            request.user.save()

            BalanceTransaction.objects.create(
                user=request.user,
                amount=fail_count,
                transaction_type="CREDIT",
                description=f"Refund for {fail_count} failed messages in Campaign {campaign.id}"
            )

        # Final campaign status
        if success_count == required_credits:
            campaign.status = "COMPLETED"
        elif success_count > 0:
            campaign.status = "PARTIAL"
        else:
            campaign.status = "FAILED"

        campaign.save()

    return JsonResponse({
        "status": "success",
        "message": f"{success_count} Message(s) Sent Successfully!",
        "campaign_id": campaign.id
    })

from reports.models import Report
from .models import Campaign, CampaignRecipient
import csv

def campaign_detail(request, campaign_id):

    campaign = Campaign.objects.get(id=campaign_id)
    recipients = campaign.recipients.all()

    total = recipients.count()
    sent = recipients.filter(status="DELIVERED").count()
    failed = recipients.filter(status="FAILED").count()

    # 👇 ADD THIS BLOCK
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
                status = row.get("status")

                try:
                    recipient = CampaignRecipient.objects.get(
                        campaign=campaign,
                        mobile_number=number
                    )

                    if status.upper() == "DELIVERED":
                        recipient.status = "DELIVERED"
                    else:
                        recipient.status = "FAILED"

                    recipient.save()

                except CampaignRecipient.DoesNotExist:
                    pass

    return render(request, "campaigns/campaign_detail.html", {
        "campaign": campaign,
        "recipients": recipients,
        "total": total,
        "sent": sent,
        "failed": failed,
        "success_rate": success_rate,   # 👈 ADD THIS
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


from django.shortcuts import redirect
import requests
from django.conf import settings


def retry_failed(request, campaign_id):

    campaign = Campaign.objects.get(id=campaign_id)

    failed_recipients = campaign.recipients.filter(status="FAILED")

    for recipient in failed_recipients:

        try:
            response = requests.get(
                f"{settings.WA_BASE_URL}/http-tokenkeyapi.php",
                params={
                    "authentic-key": settings.WA_API_KEY,
                    "route": 1,
                    "number": recipient.mobile_number,
                    "message": campaign.message
                },
                timeout=15
            )

            api_response = response.json()

            if api_response.get("Status") == "Success":
                recipient.status = "DELIVERED"
                recipient.save()

        except:
            pass

    return redirect("campaign_detail", campaign_id=campaign_id)