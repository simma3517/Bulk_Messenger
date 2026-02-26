from django.shortcuts import render
from django.db.models import Count, Q
from campaigns.models import Campaign


def reports_page(request):

    campaigns = Campaign.objects.annotate(
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