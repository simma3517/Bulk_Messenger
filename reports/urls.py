from django.urls import path
from . import views

urlpatterns = [
    path("support/", views.support_panel, name="support_panel"),
    path("upload/<int:campaign_id>/", views.upload_report, name="upload_report"),
    path("my-reports/", views.reports_page, name="reports_page"),
]