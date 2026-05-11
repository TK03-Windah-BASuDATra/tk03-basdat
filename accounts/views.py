from django.contrib import messages
from django.db import connection
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods


ROLE_NAME_MAP = {
    'customer': 'CUSTOMER',
    'organizer': 'ORGANIZER',
    'admin': 'ADMIN',
}


def _get_session_role(request):
    r = request.session.get('role')
    return r if r in ('admin', 'organizer', 'customer') else 'guest'


def _clear_reg_session(request):
    for key in [
        'reg_username', 'reg_password', 'reg_role', 'reg_step',
        'reg_full_name', 'reg_email', 'reg_phone', 'reg_existing_user_id',
        'reg_prefill',
    ]:
        request.session.pop(key, None)


def _do_register(request, full_name=None, email=None, phone=None):
    username = request.session['reg_username']
    password = request.session['reg_password']
    role = request.session['reg_role']
    role_name = ROLE_NAME_MAP[role]
    existing_user_id = request.session.get('reg_existing_user_id')

    with connection.cursor() as cur:
        if existing_user_id:
            user_id = existing_user_id
        else:
            cur.execute(
                'INSERT INTO user_account (username, password) VALUES (%s, %s) RETURNING user_id',
                [username, password],
            )
            user_id = str(cur.fetchone()[0])

        cur.execute('SELECT role_id FROM role WHERE role_name = %s', [role_name])
        role_id = str(cur.fetchone()[0])
        cur.execute('INSERT INTO account_role (role_id, user_id) VALUES (%s, %s)', [role_id, user_id])

        if role == 'admin':
            return

        if not full_name:
            cur.execute(
                'SELECT full_name, contact_email, phone_number FROM customer WHERE user_id = %s',
                [user_id],
            )
            row = cur.fetchone()
            if not row:
                cur.execute(
                    'SELECT organizer_name, contact_email, phone_number FROM organizer WHERE user_id = %s',
                    [user_id],
                )
                row = cur.fetchone()
            if row:
                full_name, email, phone = row

        if role == 'customer':
            cur.execute(
                'INSERT INTO customer (full_name, phone_number, contact_email, user_id) VALUES (%s, %s, %s, %s)',
                [full_name, phone, email, user_id],
            )
        elif role == 'organizer':
            cur.execute(
                'INSERT INTO organizer (organizer_name, contact_email, phone_number, user_id) VALUES (%s, %s, %s, %s)',
                [full_name, email, phone, user_id],
            )


# ──────────────────────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────────────────────

def login_view(request):
    from .forms import LoginForm

    if _get_session_role(request) != 'guest':
        return redirect('dashboard')

    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        role = form.cleaned_data['role']
        role_name = ROLE_NAME_MAP[role]

        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT ua.user_id
                FROM user_account ua
                JOIN account_role ar ON ar.user_id = ua.user_id
                JOIN role r ON r.role_id = ar.role_id
                WHERE ua.username = %s
                  AND ua.password = %s
                  AND r.role_name = %s
                """,
                [username, password, role_name],
            )
            row = cur.fetchone()

        if not row:
            messages.error(request, 'Username, password, atau role tidak valid.')
            return render(request, 'login.html', {'form': form})

        request.session['user_id'] = str(row[0])
        request.session['username'] = username
        request.session['role'] = role
        return redirect('dashboard')

    return render(request, 'login.html', {'form': form})


# ──────────────────────────────────────────────────────────────
# REGISTER (multi-step)
# ──────────────────────────────────────────────────────────────

def register_view(request):
    if _get_session_role(request) != 'guest':
        return redirect('dashboard')

    if request.method == 'POST':
        # ── BACK ─────────────────────────────────────────────
        if request.POST.get('action') == 'back':
            back_to = int(request.POST.get('back_to', 1))
            if back_to == 1:
                _clear_reg_session(request)
                return render(request, 'register.html', {'step': 1})
            elif back_to == 2:
                request.session.pop('reg_prefill', None)
                request.session.pop('reg_role', None)
                return render(request, 'register.html', {'step': 2})

        current_step = int(request.POST.get('step', 1))

        # ── STEP 1 ──────────────────────────────────────────
        if current_step == 1:
            username = request.POST.get('username', '').strip()
            password1 = request.POST.get('password1', '').strip()
            password2 = request.POST.get('password2', '').strip()
            agree_terms = request.POST.get('agree_terms')
            errors = {}

            # basic validation
            if not username:
                errors['username'] = 'Username wajib diisi.'
            if not password1:
                errors['password1'] = 'Password wajib diisi.'
            if password1 and password1 != password2:
                errors['password2'] = 'Password tidak cocok.'
            if not agree_terms:
                errors['agree_terms'] = 'Anda harus menyetujui Syarat & Ketentuan.'

            # VALIDASI USER EXISTING DI SINI
            existing_user_id = None

            if username and password1:
                with connection.cursor() as cur:
                    cur.execute(
                        'SELECT user_id, password FROM user_account WHERE username = %s',
                        [username],
                    )
                    row = cur.fetchone()

                    if row:
                        existing_user_id, existing_password = str(row[0]), row[1]

                        # ❌ password salah → STOP di step 1
                        if existing_password != password1:
                            errors['password1'] = 'Password tidak cocok dengan akun yang sudah ada.'

            # kalau ada error -> stop
            if errors:
                return render(request, 'register.html', {
                    'step': 1,
                    'errors': errors,
                    'prev': request.POST,
                })

            # simpan session
            request.session['reg_username'] = username
            request.session['reg_password'] = password1
            request.session['reg_existing_user_id'] = existing_user_id
            request.session['reg_step'] = 2

            # kalau user lama → kasih info
            if existing_user_id:
                messages.info(request, "Akun ditemukan. Anda akan menambahkan role baru.")

            return render(request, 'register.html', {'step': 2})

        # ── STEP 2 ──────────────────────────────────────────
        elif current_step == 2:
            role = request.POST.get('role', '')
            if role not in ('customer', 'organizer', 'admin'):
                return render(request, 'register.html', {
                    'step': 2,
                    'errors': {'role': 'Pilih role yang valid.'},
                })

            username = request.session.get('reg_username')
            role_name = ROLE_NAME_MAP[role]
            existing_user_id = request.session.get('reg_existing_user_id')
            prefill = None

            with connection.cursor() as cur:
                # kalau user lama → cek role sudah ada atau belum
                if existing_user_id:
                    cur.execute(
                        """
                        SELECT 1 FROM account_role ar
                        JOIN role r ON r.role_id = ar.role_id
                        WHERE ar.user_id = %s AND r.role_name = %s
                        """,
                        [existing_user_id, role_name],
                    )
                    if cur.fetchone():
                        return render(request, 'register.html', {
                            'step': 2,
                            'errors': {'role': f'Akun ini sudah memiliki role {role}. Silakan login.'},
                        })

                    # prefill data
                    if role != 'admin':
                        cur.execute(
                            'SELECT full_name, contact_email, phone_number FROM customer WHERE user_id = %s',
                            [existing_user_id],
                        )
                        row = cur.fetchone()
                        if not row:
                            cur.execute(
                                'SELECT organizer_name, contact_email, phone_number FROM organizer WHERE user_id = %s',
                                [existing_user_id],
                            )
                            row = cur.fetchone()

                        if row:
                            prefill = {
                                'full_name': row[0],
                                'email': row[1],
                                'phone_number': row[2],
                            }

            request.session['reg_role'] = role
            request.session['reg_step'] = 3

            if prefill:
                request.session['reg_prefill'] = prefill

            return render(request, 'register.html', {
                'step': 3,
                'role': role,
                'prefill': prefill,
                'readonly': prefill is not None or role == 'admin',
            })

        # ── STEP 3 ──────────────────────────────────────────
        elif current_step == 3:
            role = request.session.get('reg_role')
            is_admin = role == 'admin'
            has_prefill = request.session.get('reg_prefill') is not None
            readonly = is_admin or has_prefill

            if readonly:
                prefill = request.session.get('reg_prefill')
                full_name = prefill['full_name'] if prefill else None
                email = prefill['email'] if prefill else None
                phone_number = prefill['phone_number'] if prefill else None

                _do_register(request, full_name=full_name, email=email, phone=phone_number)
                _clear_reg_session(request)
                return render(request, 'register.html', {'step': 4})

            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone_number = request.POST.get('phone_number', '').strip()
            errors = {}

            if not full_name:
                errors['full_name'] = 'Nama lengkap wajib diisi.'
            if not email:
                errors['email'] = 'Email wajib diisi.'
            if not phone_number:
                errors['phone_number'] = 'Nomor telepon wajib diisi.'

            if errors:
                return render(request, 'register.html', {
                    'step': 3,
                    'role': role,
                    'errors': errors,
                    'prev': request.POST,
                })

            _do_register(request, full_name=full_name, email=email, phone=phone_number)
            _clear_reg_session(request)
            return render(request, 'register.html', {'step': 4})

    # GET
    _clear_reg_session(request)
    return render(request, 'register.html', {'step': 1})


# ──────────────────────────────────────────────────────────────
# LOGOUT
# ──────────────────────────────────────────────────────────────

def logout_view(request):
    request.session.flush()
    messages.success(request, 'Logout berhasil.')
    return redirect(reverse('accounts:login'))


# ──────────────────────────────────────────────────────────────
# PROFILE
# ──────────────────────────────────────────────────────────────

@require_http_methods(['GET'])
def profile(request):
    role = _get_session_role(request)
    if role == 'guest':
        return redirect(reverse('accounts:login'))

    user_id = request.session['user_id']

    with connection.cursor() as cur:
        cur.execute('SELECT username FROM user_account WHERE user_id = %s', [user_id])
        row = cur.fetchone()
        username = row[0] if row else ''

        full_name = phone_number = email = organizer_name = ''
        display_name = username

        if role == 'customer':
            cur.execute(
                'SELECT full_name, phone_number, contact_email FROM customer WHERE user_id = %s',
                [user_id],
            )
            row = cur.fetchone()
            if row:
                full_name, phone_number, email = row
                display_name = full_name

        elif role == 'organizer':
            cur.execute(
                'SELECT organizer_name, contact_email, phone_number FROM organizer WHERE user_id = %s',
                [user_id],
            )
            row = cur.fetchone()
            if row:
                organizer_name, email, phone_number = row
                display_name = organizer_name

    return render(request, 'profile.html', {
        'username': username,
        'display_name': display_name,
        'full_name': full_name,
        'phone_number': phone_number,
        'contact_email': email,
        'organizer_name': organizer_name,
    })


@require_POST
def profile_update(request):
    role = _get_session_role(request)
    if role == 'guest':
        return redirect(reverse('accounts:login'))

    user_id = request.session['user_id']

    if role == 'customer':
        with connection.cursor() as cur:
            cur.execute(
                """
                UPDATE customer
                SET full_name = %s, phone_number = %s, contact_email = %s
                WHERE user_id = %s
                """,
                [
                    request.POST.get('full_name', '').strip(),
                    request.POST.get('phone_number', '').strip(),
                    request.POST.get('email', '').strip(),
                    user_id,
                ],
            )

    elif role == 'organizer':
        with connection.cursor() as cur:
            cur.execute(
                """
                UPDATE organizer
                SET organizer_name = %s, phone_number = %s, contact_email = %s
                WHERE user_id = %s
                """,
                [
                    request.POST.get('organizer_name', '').strip(),
                    request.POST.get('phone_number', '').strip(),
                    request.POST.get('email', '').strip(),
                    user_id,
                ],
            )

    messages.success(request, 'Profil berhasil diperbarui.')
    return redirect(reverse('accounts:profile'))


@require_POST
def profile_password(request):
    role = _get_session_role(request)
    if role == 'guest':
        return redirect(reverse('accounts:login'))

    user_id = request.session['user_id']
    old_password = request.POST.get('old_password', '')
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')

    if new_password != confirm_password:
        messages.error(request, 'Password baru tidak cocok.')
        return redirect(reverse('accounts:profile'))

    with connection.cursor() as cur:
        cur.execute('SELECT password FROM user_account WHERE user_id = %s', [user_id])
        row = cur.fetchone()

        if not row or row[0] != old_password:
            messages.error(request, 'Password lama salah.')
            return redirect(reverse('accounts:profile'))

        cur.execute(
            'UPDATE user_account SET password = %s WHERE user_id = %s',
            [new_password, user_id],
        )

    messages.success(request, 'Password berhasil diperbarui.')
    return redirect(reverse('accounts:profile'))