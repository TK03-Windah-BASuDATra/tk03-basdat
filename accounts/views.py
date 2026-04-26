from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Username atau password salah.")

    return render(request, "accounts/login.html")


def pilih_role_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    return render(request, "accounts/pilih_role.html")


def register_view(request, role):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if role not in ["organizer", "customer"]:
        messages.error(request, "Role tidak valid.")
        return redirect("pilih_role")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(role=role)
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {
        "form": form,
        "role": role,
    })


def logout_view(request):
    logout(request)
    return redirect("login")