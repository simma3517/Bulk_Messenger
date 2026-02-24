from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),

    # When someone visits "/"
    path('', lambda request: redirect('login')),

    # Accounts URLs
    path('', include('accounts.urls')),

    # Campaign URLs
    path('campaigns/', include('campaigns.urls')),
]