from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Sum
from campaigns.models import CampaignRecipient
from .models import BalanceTransaction

User = get_user_model()


# ===============================
# 🔐 ROLE DECORATOR
# ===============================

def role_required(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):

            # Not logged in
            if not request.user.is_authenticated:
                return redirect("login")

            # SUPER ADMIN BYPASS
            if request.user.role == "SUPER_ADMIN":
                return view_func(request, *args, **kwargs)

            if request.user.role not in roles:
                return HttpResponseForbidden("You are not authorized to access this page.")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ===============================
# 🔑 LOGIN / LOGOUT
# ===============================

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


# ===============================
# 📊 DASHBOARD
# ===============================

@login_required
def dashboard_view(request):

    if request.user.role == "USER":
        recipients = CampaignRecipient.objects.filter(
            campaign__user=request.user
        )

    elif request.user.role == "MANAGER":
        recipients = CampaignRecipient.objects.filter(
            campaign__user__parent=request.user
        )

    else:
        # SUPPORT & SUPER_ADMIN
        recipients = CampaignRecipient.objects.all()

    total_submitted = recipients.count()
    delivered_count = recipients.filter(status="DELIVERED").count()
    failed_count = recipients.filter(status="FAILED").count()

    # Net Credit Used
    debit = BalanceTransaction.objects.filter(
        user=request.user,
        transaction_type="DEBIT"
    ).aggregate(total=Sum("amount"))["total"] or 0

    credit = BalanceTransaction.objects.filter(
        user=request.user,
        transaction_type="CREDIT"
    ).aggregate(total=Sum("amount"))["total"] or 0

    credit_used = debit - credit

    context = {
        "total_submitted": total_submitted,
        "delivered_count": delivered_count,
        "failed_count": failed_count,
        "credit_used": credit_used,
    }

    return render(request, "dashboards/main_dashboard.html", context)


# ===============================
# 👤 MY ACCOUNT
# ===============================

@login_required
@role_required("USER", "MANAGER")
def my_account(request):

    user = request.user

    total_debit = BalanceTransaction.objects.filter(
        user=user,
        transaction_type="DEBIT"
    ).aggregate(total=Sum("amount"))["total"] or 0

    total_credit = BalanceTransaction.objects.filter(
        user=user,
        transaction_type="CREDIT"
    ).aggregate(total=Sum("amount"))["total"] or 0

    context = {
        "user": user,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "net_usage": total_debit - total_credit,
    }

    return render(request, "accounts/my_account.html", context)


# ===============================
# 👥 USER MANAGEMENT
# ===============================

@login_required
@role_required("MANAGER", "SUPER_ADMIN")
def user_management(request):
    users = User.objects.all()
    return render(request, "accounts/user_management.html", {"users": users})


# ===============================
# ➕ ADD ACCOUNT (ONLY ONE)
# ===============================

@login_required
@role_required("MANAGER", "SUPER_ADMIN")
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

        # Safe role assignment
        user.role = role if role else "USER"
        user.mobile = mobile
        user.save()

        messages.success(request, "Account Created Successfully!")
        return redirect("user_management")

    return render(request, "accounts/add_account.html")


# ===============================
# 💳 TRANSACTION HISTORY
# ===============================
from django.db.models import Sum

@login_required
def transaction_history(request):

    if request.user.role == "SUPER_ADMIN":
        transactions = BalanceTransaction.objects.all().order_by("-created_at")
    elif request.user.role == "MANAGER":
        transactions = BalanceTransaction.objects.filter(
            user__parent=request.user
        ).order_by("-created_at")
    else:
        transactions = BalanceTransaction.objects.filter(
            user=request.user
        ).order_by("-created_at")

    total_credit = transactions.filter(
        transaction_type="CREDIT"
    ).aggregate(total=Sum("amount"))["total"] or 0

    total_debit = transactions.filter(
        transaction_type="DEBIT"
    ).aggregate(total=Sum("amount"))["total"] or 0

    return render(request, "accounts/transactions.html", {
        "transactions": transactions,
        "total_credit": total_credit,
        "total_debit": total_debit,
    })


from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

User = get_user_model()

@login_required
def create_user(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        print("ROLE RECEIVED:", role)  # DEBUG

        if not username or not password:
            messages.error(request, "Username and Password required.")
            return redirect("add_user")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("add_user")

        # 🔥 CREATE USER
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        # 🔥 FORCE ROLE SAVE
        if role in dict(User.Roles.choices).keys():
            user.role = role
        else:
            user.role = User.Roles.USER

        user.save()

        messages.success(request, f"User created with role: {user.role}")
        return redirect("user_management")

    return render(request, "accounts/add_user.html")

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from accounts.models import User, BalanceTransaction
from django.contrib.auth.decorators import login_required

from decimal import Decimal
from django.shortcuts import get_object_or_404

@login_required
def add_balance(request, user_id):

    if request.user.role not in ["SUPER_ADMIN", "MANAGER"]:
        messages.error(request, "Permission Denied")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        amount = Decimal(request.POST.get("amount"))

        if amount > 0:
            user.balance += amount
            user.save()

            BalanceTransaction.objects.create(
                user=user,
                amount=amount,
                transaction_type="CREDIT",
                description=f"Balance added by {request.user.username}"
            )

            messages.success(request, "Balance Added Successfully")

        return redirect("user_management")

    return render(request, "accounts/add_balance.html", {"user": user})

@login_required
def deduct_balance(request, user_id):

    if request.user.role not in ["SUPER_ADMIN", "MANAGER"]:
        messages.error(request, "Permission Denied")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        amount = Decimal(request.POST.get("amount"))

        if amount <= 0:
            messages.error(request, "Invalid amount")
            return redirect("user_management")

        if user.balance < amount:
            messages.error(request, "Insufficient balance")
            return redirect("user_management")

        user.balance -= amount
        user.save()

        BalanceTransaction.objects.create(
            user=user,
            amount=amount,
            transaction_type="DEBIT",
            description=f"Balance deducted by {request.user.username}"
        )

        messages.success(request, "Balance Deducted Successfully")

        return redirect("user_management")

    return render(request, "accounts/deduct_balance.html", {"user": user})