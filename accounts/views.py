from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.db import connection
from .forms import RegisterForm
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.views.decorators.http import require_http_methods



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

    return render(request, "login.html", {
        "role": current_role,
    })


def pilih_role_view(request):
    current_role = _safe_role(request.GET.get("role", "guest"))

    if current_role != "guest":
        return redirect(f"{reverse('dashboard')}?role={current_role}")

    return render(request, "pilih_role.html", {
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

    return render(request, "register.html", {
        "form": form,
        "role": role,
    })


def logout_view(request):
    messages.success(request, "Simulasi logout berhasil.")
    return redirect(f"{reverse('login')}?role=guest")

# PROFILE VIEW

@require_http_methods(["GET"])
@require_http_methods(["GET"])
def profile(request):
    role = request.GET.get('role', 'guest')
    if role == 'customer':
        user_id = '00000000-0000-0000-0000-000000000001'
    elif role == 'organizer':
        user_id = '00000000-0000-0000-0000-000000000007'
    elif role == 'admin':
        user_id = '00000000-0000-0000-0000-000000000011'
    else:
        return redirect('/?role=guest')

    with connection.cursor() as cur:
        cur.execute("SELECT username FROM user_account WHERE user_id = %s", [user_id])
        row = cur.fetchone()
        username = row[0] if row else ''

        full_name = phone_number = organizer_name = contact_email = ''
        display_name = username

        if role == 'customer':
            cur.execute("SELECT full_name, phone_number FROM customer WHERE user_id = %s", [user_id])
            row = cur.fetchone()
            if row:
                full_name, phone_number = row
                display_name = full_name

        elif role == 'organizer':
            cur.execute("SELECT organizer_name, contact_email FROM organizer WHERE user_id = %s", [user_id])
            row = cur.fetchone()
            if row:
                organizer_name, contact_email = row
                display_name = organizer_name

    return render(request, 'profile.html', {
        'username': username,
        'display_name': display_name,
        'full_name': full_name,
        'phone_number': phone_number,
        'organizer_name': organizer_name,
        'contact_email': contact_email,
    })


@require_POST
def profile_update(request):
    role = request.GET.get('role', 'guest')
    if role == 'customer':
        user_id = '00000000-0000-0000-0000-000000000001'
        full_name = request.POST.get('full_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE customer SET full_name = %s, phone_number = %s WHERE user_id = %s
            """, [full_name, phone_number, user_id])

    elif role == 'organizer':
        user_id = '00000000-0000-0000-0000-000000000007'
        organizer_name = request.POST.get('organizer_name', '').strip()
        contact_email = request.POST.get('contact_email', '').strip()
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE organizer SET organizer_name = %s, contact_email = %s WHERE user_id = %s
            """, [organizer_name, contact_email, user_id])

    return redirect(f'/accounts/profile/?role={role}')


@require_POST
def profile_password(request):
    role = request.GET.get('role', 'guest')
    if role == 'customer':
        user_id = '00000000-0000-0000-0000-000000000001'
    elif role == 'organizer':
        user_id = '00000000-0000-0000-0000-000000000007'
    elif role == 'admin':
        user_id = '00000000-0000-0000-0000-000000000011'
    else:
        return redirect('/')

    old_password = request.POST.get('old_password', '')
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')

    if new_password != confirm_password:
        messages.error(request, 'Password baru tidak cocok.')
        return redirect(f'accounts/profile/?role={role}')

    with connection.cursor() as cur:
        cur.execute("SELECT password FROM user_account WHERE user_id = %s", [user_id])
        row = cur.fetchone()
        if not row or row[0] != old_password:
            messages.error(request, 'Password lama salah.')
            return redirect(f'/accounts/profile/?role={role}')

        cur.execute("UPDATE user_account SET password = %s WHERE user_id = %s", [new_password, user_id])

    messages.success(request, 'Password berhasil diperbarui.')
    return redirect(f'/accounts/profile/?role={role}')