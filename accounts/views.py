from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "login.html", {"error": "Invalid credentials"})

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
       return render(request, "dashboards/main_dashboard.html")

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

def add_account(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        role = request.POST.get("role")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("add_account")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("add_account")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.role = role
        user.mobile = mobile
        user.save()

        messages.success(request, "Account Created Successfully!")
        return redirect("user_management")

    return render(request, "accounts/add_account.html")

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()


@login_required
def user_management(request):
    users = User.objects.all()
    return render(request, "accounts/user_management.html", {"users": users})


@login_required
def create_user(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("user_management")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # If you have role field in custom user
        if hasattr(user, "role"):
            user.role = role
            user.save()

        messages.success(request, "User Created Successfully!")
        return redirect("user_management")

    return redirect("user_management")

@login_required
def add_user(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.role = role
        user.save()

        return redirect("user_management")

    return render(request, "accounts/add_user.html")