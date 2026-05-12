from django.contrib import messages
from django.db import DatabaseError, connection, transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

ROLE_NAME = {
    'customer': 'CUSTOMER',
    'organizer': 'ORGANIZER',
    'admin': 'ADMIN',
}

VALID_ROLES = tuple(ROLE_NAME.keys())


def _get_session_role(request):
    role = request.session.get('role')
    return role if role in VALID_ROLES else 'guest'


def _dashboard_url(role):
    return f"{reverse('dashboard')}?role={role}"


def _clear_reg_session(request):
    for key in [
        'reg_username', 'reg_password', 'reg_role', 'reg_step',
        'reg_full_name', 'reg_email', 'reg_phone', 'reg_prefill',
        'reg_existing_user_id',
    ]:
        request.session.pop(key, None)


def _database_error_message(exc):
    message = str(exc).strip()
    if not message:
        return 'Terjadi kesalahan database.'

    first_line = message.splitlines()[0].strip()
    for prefix in ('ERROR:  ', 'ERROR:', 'Error:'):
        if first_line.startswith(prefix):
            first_line = first_line[len(prefix):].strip()
    return first_line or 'Terjadi kesalahan database.'


def _render_register_error_step1(request, message, username='', page_title='Daftar Akun'):
    return render(request, 'register.html', {
        'step': 1,
        'errors': {'username': message},
        'prefill': {'username': username},
        'prev': {'username': username},
        'role': 'guest',
        'page_title': page_title,
    })


def _validate_username_from_db(username):
    # Function ini harus dibuat di PostgreSQL dan tersedia lewat search_path schema project.
    # Validasi duplikat case-insensitive dan karakter username dilakukan oleh database.
    with connection.cursor() as cur:
        cur.execute('SELECT validate_username(%s, NULL::uuid)', [username])


def _role_id_for(cur, role):
    role_name = ROLE_NAME[role]
    cur.execute('SELECT role_id FROM role WHERE role_name = %s', [role_name])
    row = cur.fetchone()
    if not row:
        raise DatabaseError(f'Role {role_name} tidak ditemukan di tabel role.')
    return str(row[0])


def _create_user_with_role(request, full_name=None, email=None, phone=None):
    """Register akun baru. Username wajib belum pernah terdaftar."""
    username = request.session['reg_username']
    password = request.session['reg_password']
    role = request.session['reg_role']

    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute(
                'INSERT INTO user_account (username, password) VALUES (%s, %s) RETURNING user_id',
                [username, password],
            )
            user_id = str(cur.fetchone()[0])

            role_id = _role_id_for(cur, role)
            cur.execute(
                'INSERT INTO account_role (role_id, user_id) VALUES (%s, %s)',
                [role_id, user_id],
            )

            if role == 'customer':
                cur.execute(
                    '''
                    INSERT INTO customer (full_name, phone_number, contact_email, user_id)
                    VALUES (%s, %s, %s, %s)
                    ''',
                    [full_name, phone, email, user_id],
                )
            elif role == 'organizer':
                cur.execute(
                    '''
                    INSERT INTO organizer (organizer_name, contact_email, phone_number, user_id)
                    VALUES (%s, %s, %s, %s)
                    ''',
                    [full_name, email, phone, user_id],
                )


def _add_role_to_existing_user(request, full_name=None, email=None, phone=None):
    """Flow opsional tambah role. Tidak insert user_account lagi."""
    user_id = request.session['reg_existing_user_id']
    role = request.session['reg_role']

    with transaction.atomic():
        with connection.cursor() as cur:
            role_id = _role_id_for(cur, role)

            cur.execute(
                '''
                SELECT 1
                FROM account_role ar
                WHERE ar.user_id = %s AND ar.role_id = %s
                ''',
                [user_id, role_id],
            )
            if cur.fetchone():
                raise DatabaseError(f'Akun ini sudah memiliki role {role}.')

            cur.execute(
                'INSERT INTO account_role (role_id, user_id) VALUES (%s, %s)',
                [role_id, user_id],
            )

            if role == 'customer':
                cur.execute('SELECT 1 FROM customer WHERE user_id = %s', [user_id])
                if not cur.fetchone():
                    cur.execute(
                        '''
                        INSERT INTO customer (full_name, phone_number, contact_email, user_id)
                        VALUES (%s, %s, %s, %s)
                        ''',
                        [full_name, phone, email, user_id],
                    )
            elif role == 'organizer':
                cur.execute('SELECT 1 FROM organizer WHERE user_id = %s', [user_id])
                if not cur.fetchone():
                    cur.execute(
                        '''
                        INSERT INTO organizer (organizer_name, contact_email, phone_number, user_id)
                        VALUES (%s, %s, %s, %s)
                        ''',
                        [full_name, email, phone, user_id],
                    )


# ──────────────────────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────────────────────

def login_view(request):
    from .forms import LoginForm

    if _get_session_role(request) != 'guest':
        return redirect(_dashboard_url(_get_session_role(request)))

    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username'].strip()
        password = form.cleaned_data['password']
        role = form.cleaned_data['role']
        role_name = ROLE_NAME[role]

        with connection.cursor() as cur:
            cur.execute(
                '''
                SELECT ua.user_id
                FROM user_account ua
                JOIN account_role ar ON ar.user_id = ua.user_id
                JOIN role r ON r.role_id = ar.role_id
                WHERE LOWER(ua.username) = LOWER(%s)
                  AND ua.password = %s
                  AND r.role_name = %s
                ''',
                [username, password, role_name],
            )
            row = cur.fetchone()

        if not row:
            messages.error(request, 'Username, password, atau role tidak valid.')
            return render(request, 'login.html', {'form': form, 'role': 'guest'})

        request.session['user_id'] = str(row[0])
        request.session['username'] = username
        request.session['role'] = role
        return redirect(_dashboard_url(role))

    return render(request, 'login.html', {'form': form, 'role': 'guest'})


# ──────────────────────────────────────────────────────────────
# REGISTER AKUN BARU
# ──────────────────────────────────────────────────────────────

def register_view(request):
    if _get_session_role(request) != 'guest':
        return redirect(_dashboard_url(_get_session_role(request)))

    page_title = 'Daftar Akun'

    if request.method == 'POST':
        if request.POST.get('action') == 'back':
            back_to = int(request.POST.get('back_to', 1))
            if back_to == 1:
                _clear_reg_session(request)
                return render(request, 'register.html', {'step': 1, 'role': 'guest', 'page_title': page_title})
            if back_to == 2:
                request.session.pop('reg_role', None)
                return render(request, 'register.html', {'step': 2, 'role': 'guest', 'page_title': page_title})

        current_step = int(request.POST.get('step', 1))

        if current_step == 1:
            username = request.POST.get('username', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            agree_terms = request.POST.get('agree_terms')
            errors = {}

            if not username:
                errors['username'] = 'Username wajib diisi.'
            if not password1:
                errors['password1'] = 'Password wajib diisi.'
            elif len(password1) < 6:
                errors['password1'] = 'Password minimal 6 karakter.'
            if password1 and password1 != password2:
                errors['password2'] = 'Password tidak cocok.'
            if not agree_terms:
                errors['agree_terms'] = 'Anda harus menyetujui Syarat & Ketentuan.'

            if username and 'username' not in errors:
                try:
                    _validate_username_from_db(username)
                except DatabaseError as exc:
                    errors['username'] = _database_error_message(exc)

            if errors:
                return render(request, 'register.html', {
                    'step': 1,
                    'errors': errors,
                    'prefill': {'username': username},
                    'prev': {'username': username},
                    'role': 'guest',
                    'page_title': page_title,
                })

            request.session['reg_username'] = username
            request.session['reg_password'] = password1
            request.session['reg_step'] = 2
            return render(request, 'register.html', {'step': 2, 'role': 'guest', 'page_title': page_title})

        if current_step == 2:
            role = request.POST.get('role', '')
            if role not in VALID_ROLES:
                return render(request, 'register.html', {
                    'step': 2,
                    'errors': {'role': 'Pilih role yang valid.'},
                    'role': 'guest',
                    'page_title': page_title,
                })

            if not request.session.get('reg_username') or not request.session.get('reg_password'):
                return _render_register_error_step1(
                    request,
                    'Sesi pendaftaran habis. Silakan isi ulang username dan password.',
                    page_title=page_title,
                )

            request.session['reg_role'] = role
            request.session['reg_step'] = 3
            return render(request, 'register.html', {
                'step': 3,
                'role': role,
                'readonly': role == 'admin',
                'page_title': page_title,
            })

        if current_step == 3:
            role = request.session.get('reg_role')
            if role not in VALID_ROLES:
                return render(request, 'register.html', {
                    'step': 2,
                    'errors': {'role': 'Pilih role terlebih dahulu.'},
                    'role': 'guest',
                    'page_title': page_title,
                })

            full_name = email = phone_number = None
            errors = {}

            if role != 'admin':
                full_name = request.POST.get('full_name', '').strip()
                email = request.POST.get('email', '').strip()
                phone_number = request.POST.get('phone_number', '').strip()

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
                    'readonly': role == 'admin',
                    'prefill': {
                        'full_name': full_name or '',
                        'email': email or '',
                        'phone_number': phone_number or '',
                    },
                    'page_title': page_title,
                })

            try:
                _create_user_with_role(request, full_name=full_name, email=email, phone=phone_number)
            except DatabaseError as exc:
                username = request.session.get('reg_username', '')
                _clear_reg_session(request)
                return _render_register_error_step1(request, _database_error_message(exc), username, page_title)

            _clear_reg_session(request)
            return render(request, 'register.html', {'step': 4, 'role': 'guest', 'page_title': page_title})

    _clear_reg_session(request)
    return render(request, 'register.html', {'step': 1, 'role': 'guest', 'page_title': page_title})


# ──────────────────────────────────────────────────────────────
# OPSIONAL: TAMBAH ROLE PADA AKUN YANG SUDAH ADA
# ──────────────────────────────────────────────────────────────

def add_role_view(request):
    if _get_session_role(request) != 'guest':
        return redirect(_dashboard_url(_get_session_role(request)))

    page_title = 'Tambah Role'

    if request.method == 'POST':
        if request.POST.get('action') == 'back':
            back_to = int(request.POST.get('back_to', 1))
            if back_to == 1:
                _clear_reg_session(request)
                return render(request, 'register.html', {'step': 1, 'role': 'guest', 'page_title': page_title})
            if back_to == 2:
                request.session.pop('reg_role', None)
                return render(request, 'register.html', {'step': 2, 'role': 'guest', 'page_title': page_title})

        current_step = int(request.POST.get('step', 1))

        if current_step == 1:
            username = request.POST.get('username', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            agree_terms = request.POST.get('agree_terms')
            errors = {}
            existing_user_id = None

            if not username:
                errors['username'] = 'Username wajib diisi.'
            if not password1:
                errors['password1'] = 'Password wajib diisi.'
            elif len(password1) < 6:
                errors['password1'] = 'Password minimal 6 karakter.'
            if password1 and password1 != password2:
                errors['password2'] = 'Password tidak cocok.'
            if not agree_terms:
                errors['agree_terms'] = 'Anda harus menyetujui Syarat & Ketentuan.'

            if username and password1 and not errors:
                with connection.cursor() as cur:
                    cur.execute(
                        '''
                        SELECT user_id, password
                        FROM user_account
                        WHERE LOWER(username) = LOWER(%s)
                        ''',
                        [username],
                    )
                    row = cur.fetchone()

                if not row:
                    errors['username'] = 'Akun dengan username ini tidak ditemukan.'
                else:
                    existing_user_id, existing_password = str(row[0]), row[1]
                    if existing_password != password1:
                        errors['password1'] = 'Password tidak cocok dengan akun yang sudah ada.'

            if errors:
                return render(request, 'register.html', {
                    'step': 1,
                    'errors': errors,
                    'prefill': {'username': username},
                    'prev': {'username': username},
                    'role': 'guest',
                    'page_title': page_title,
                })

            request.session['reg_username'] = username
            request.session['reg_password'] = password1
            request.session['reg_existing_user_id'] = existing_user_id
            request.session['reg_step'] = 2
            messages.info(request, 'Akun ditemukan. Anda akan menambahkan role baru.')
            return render(request, 'register.html', {'step': 2, 'role': 'guest', 'page_title': page_title})

        if current_step == 2:
            role = request.POST.get('role', '')
            existing_user_id = request.session.get('reg_existing_user_id')

            if role not in VALID_ROLES:
                return render(request, 'register.html', {
                    'step': 2,
                    'errors': {'role': 'Pilih role yang valid.'},
                    'role': 'guest',
                    'page_title': page_title,
                })
            if not existing_user_id:
                return _render_register_error_step1(
                    request,
                    'Sesi tambah role habis. Silakan isi ulang username dan password.',
                    page_title=page_title,
                )

            role_name = ROLE_NAME[role]
            prefill = None
            with connection.cursor() as cur:
                cur.execute(
                    '''
                    SELECT 1
                    FROM account_role ar
                    JOIN role r ON r.role_id = ar.role_id
                    WHERE ar.user_id = %s AND r.role_name = %s
                    ''',
                    [existing_user_id, role_name],
                )
                if cur.fetchone():
                    return render(request, 'register.html', {
                        'step': 2,
                        'errors': {'role': f'Akun ini sudah memiliki role {role}. Silakan login.'},
                        'role': 'guest',
                        'page_title': page_title,
                    })

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
                'page_title': page_title,
            })

        if current_step == 3:
            role = request.session.get('reg_role')
            if role not in VALID_ROLES:
                return render(request, 'register.html', {
                    'step': 2,
                    'errors': {'role': 'Pilih role terlebih dahulu.'},
                    'role': 'guest',
                    'page_title': page_title,
                })

            prefill = request.session.get('reg_prefill')
            readonly = role == 'admin' or prefill is not None

            if readonly:
                full_name = prefill['full_name'] if prefill else None
                email = prefill['email'] if prefill else None
                phone_number = prefill['phone_number'] if prefill else None
            else:
                full_name = request.POST.get('full_name', '').strip()
                email = request.POST.get('email', '').strip()
                phone_number = request.POST.get('phone_number', '').strip()

            errors = {}
            if role != 'admin' and not readonly:
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
                    'readonly': role == 'admin',
                    'prefill': {
                        'full_name': full_name or '',
                        'email': email or '',
                        'phone_number': phone_number or '',
                    },
                    'page_title': page_title,
                })

            try:
                _add_role_to_existing_user(request, full_name=full_name, email=email, phone=phone_number)
            except DatabaseError as exc:
                username = request.session.get('reg_username', '')
                _clear_reg_session(request)
                return _render_register_error_step1(request, _database_error_message(exc), username, page_title)

            _clear_reg_session(request)
            return render(request, 'register.html', {'step': 4, 'role': 'guest', 'page_title': page_title})

    _clear_reg_session(request)
    return render(request, 'register.html', {'step': 1, 'role': 'guest', 'page_title': page_title})


# ──────────────────────────────────────────────────────────────
# LOGOUT
# ──────────────────────────────────────────────────────────────

def logout_view(request):
    request.session.flush()
    messages.success(request, 'Logout berhasil.')
    return redirect(reverse('dashboard'))


# ──────────────────────────────────────────────────────────────
# PROFILE
# ──────────────────────────────────────────────────────────────

@require_http_methods(['GET'])
def profile(request):
    role = _get_session_role(request)
    if role == 'guest':
        return redirect(reverse('accounts:login'))

    user_id = request.session['user_id']
    username = ''
    full_name = ''
    phone_number = ''
    email = ''
    contact_email = ''
    organizer_name = ''
    display_name = ''

    with connection.cursor() as cur:
        cur.execute('SELECT username FROM user_account WHERE user_id = %s', [user_id])
        row = cur.fetchone()
        username = row[0] if row else ''
        display_name = username

        if role == 'customer':
            cur.execute(
                'SELECT full_name, phone_number, contact_email FROM customer WHERE user_id = %s',
                [user_id],
            )
            row = cur.fetchone()
            if row:
                full_name, phone_number, email = row
                contact_email = email
                display_name = full_name

        elif role == 'organizer':
            cur.execute(
                'SELECT organizer_name, contact_email, phone_number FROM organizer WHERE user_id = %s',
                [user_id],
            )
            row = cur.fetchone()
            if row:
                organizer_name, contact_email, phone_number = row
                email = contact_email
                display_name = organizer_name

    return render(request, 'profile.html', {
        'role': role,
        'username': username,
        'display_name': display_name,
        'full_name': full_name,
        'phone_number': phone_number,
        'email': email,
        'contact_email': contact_email,
        'organizer_name': organizer_name,
    })


@require_POST
def profile_update(request):
    role = _get_session_role(request)
    if role == 'guest':
        return redirect(reverse('accounts:login'))

    user_id = request.session['user_id']

    if role == 'customer':
        email = (request.POST.get('contact_email') or request.POST.get('email') or '').strip()
        with connection.cursor() as cur:
            if email:
                cur.execute(
                    '''
                    UPDATE customer
                    SET full_name = %s,
                        phone_number = %s,
                        contact_email = %s
                    WHERE user_id = %s
                    ''',
                    [
                        request.POST.get('full_name', '').strip(),
                        request.POST.get('phone_number', '').strip(),
                        email,
                        user_id,
                    ],
                )
            else:
                cur.execute(
                    '''
                    UPDATE customer
                    SET full_name = %s,
                        phone_number = %s
                    WHERE user_id = %s
                    ''',
                    [
                        request.POST.get('full_name', '').strip(),
                        request.POST.get('phone_number', '').strip(),
                        user_id,
                    ],
                )

    elif role == 'organizer':
        contact_email = (
            request.POST.get('contact_email')
            or request.POST.get('email')
            or ''
        ).strip()
        phone_number = request.POST.get('phone_number', '').strip()

        with connection.cursor() as cur:
            cur.execute(
                '''
                UPDATE organizer
                SET organizer_name = %s,
                    contact_email = %s,
                    phone_number = COALESCE(NULLIF(%s, ''), phone_number)
                WHERE user_id = %s
                ''',
                [
                    request.POST.get('organizer_name', '').strip(),
                    contact_email,
                    phone_number,
                    user_id,
                ],
            )

    messages.success(request, 'Profil berhasil diperbarui.')
    return redirect(f"{reverse('accounts:profile')}?role={role}")


@require_POST
def profile_password(request):
    role = _get_session_role(request)
    if role == 'guest':
        return redirect(reverse('accounts:login'))

    user_id = request.session['user_id']
    old_password = request.POST.get('old_password', '')
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')

    if len(new_password) < 6:
        messages.error(request, 'Password baru minimal 6 karakter.')
        return redirect(f"{reverse('accounts:profile')}?role={role}")

    if new_password != confirm_password:
        messages.error(request, 'Password baru tidak cocok.')
        return redirect(f"{reverse('accounts:profile')}?role={role}")

    with connection.cursor() as cur:
        cur.execute('SELECT password FROM user_account WHERE user_id = %s', [user_id])
        row = cur.fetchone()

        if not row or row[0] != old_password:
            messages.error(request, 'Password lama salah.')
            return redirect(f"{reverse('accounts:profile')}?role={role}")

        cur.execute(
            'UPDATE user_account SET password = %s WHERE user_id = %s',
            [new_password, user_id],
        )

    messages.success(request, 'Password berhasil diperbarui.')
    return redirect(f"{reverse('accounts:profile')}?role={role}")
