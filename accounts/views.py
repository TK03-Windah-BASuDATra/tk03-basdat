from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import RegisterForm


VALID_ROLES = ["guest", "admin", "organizer", "customer"]


def _safe_role(role, default="guest"):
    return role if role in VALID_ROLES else default


def login_view(request):
    current_role = _safe_role(request.GET.get("role", "guest"))

    if current_role != "guest":
        return redirect(f"{reverse('dashboard')}?role={current_role}")

    if request.method == "POST":
        role = _safe_role(request.POST.get("role", "customer"), "customer")
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if username and password:
            messages.success(request, f"Simulasi login berhasil sebagai {role}.")
            return redirect(f"{reverse('dashboard')}?role={role}")

        messages.error(request, "Username dan password harus diisi.")

    return render(request, "accounts/login.html", {
        "role": current_role,
    })


def pilih_role_view(request):
    current_role = _safe_role(request.GET.get("role", "guest"))

    if current_role != "guest":
        return redirect(f"{reverse('dashboard')}?role={current_role}")

    return render(request, "accounts/pilih_role.html", {
        "role": current_role,
    })


def register_view(request, role):
    current_role = _safe_role(request.GET.get("role", "guest"))

    if current_role != "guest":
        return redirect(f"{reverse('dashboard')}?role={current_role}")

    if role not in ["organizer", "customer"]:
        messages.error(request, "Role tidak valid.")
        return redirect("pilih_role")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            messages.success(request, f"Simulasi registrasi {role} berhasil.")
            return redirect(f"{reverse('dashboard')}?role={role}")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {
        "form": form,
        "role": role,
    })


def logout_view(request):
    messages.success(request, "Simulasi logout berhasil.")
    return redirect(f"{reverse('login')}?role=guest")