from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_campaign, name='create_campaign'),
    path('<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('<int:campaign_id>/download-csv/', views.download_csv, name='download_csv'),
    path('<int:campaign_id>/retry/', views.retry_failed, name='retry_failed'),
]