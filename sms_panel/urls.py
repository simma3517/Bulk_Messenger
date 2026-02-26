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
     path('reports/', include('reports.urls')), 
]
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)