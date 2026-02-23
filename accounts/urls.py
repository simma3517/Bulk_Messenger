from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/', views.dashboard_view, name="dashboard"),
    
    path('users/', views.user_management, name='user_management'),
    path('users/add/', views.add_user, name='add_user'),
]