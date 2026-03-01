from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/', views.dashboard_view, name="dashboard"),
    
    path('users/', views.user_management, name='user_management'),
    path('users/add/', views.create_user, name='add_user'),
    
    path("transactions/", views.transaction_history, name="transactions"),
    path("my-account/", views.my_account, name="my_account"),
]