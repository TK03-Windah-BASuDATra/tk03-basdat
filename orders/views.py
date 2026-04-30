# orders/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection


def _get_role(request):
    if not request.user.is_authenticated:
        return 'guest'
    if request.user.is_superuser:
        return 'admin'
    return getattr(request.user, 'role', 'customer')


@login_required
def checkout(request, event_id):

    with connection.cursor() as cur:
        cur.execute('''
            SELECT
                e.event_id,
                e.event_title,
                e.event_datetime,
                v.venue_name,
                v.venue_id
            FROM windah_basudatra.event e
            JOIN windah_basudatra.venue v ON e.venue_id = v.venue_id
            WHERE e.event_id = %s
        ''', [str(event_id)])
        row = cur.fetchone()

    if not row:
        messages.error(request, 'Event tidak ditemukan.')
        return redirect('event_list')

    event = {
        'event_id':       str(row[0]),
        'event_title':    row[1],
        'event_datetime': row[2].strftime('%Y-%m-%d · %H:%M') if row[2] else '-',
        'venue_name':     row[3],
        'venue_id':       str(row[4]),
    }

    with connection.cursor() as cur:
        cur.execute('''
            SELECT a.name
            FROM windah_basudatra.artist a
            JOIN windah_basudatra.event_artist ea ON a.artist_id = ea.artist_id
            WHERE ea.event_id = %s
            ORDER BY ea.role
        ''', [str(event_id)])
        event['artists'] = [r[0] for r in cur.fetchall()]

    with connection.cursor() as cur:
        cur.execute('''
            SELECT
                category_id,
                category_name,
                quota,
                price
            FROM windah_basudatra.ticket_category
            WHERE event_id = %s AND quota > 0
            ORDER BY price DESC
        ''', [str(event_id)])
        cols       = [c[0] for c in cur.description]
        categories = [dict(zip(cols, r)) for r in cur.fetchall()]

    for cat in categories:
        cat['category_id'] = str(cat['category_id'])
        cat['price']       = float(cat['price'])

    with connection.cursor() as cur:
        cur.execute('''
            SELECT
                seat_id,
                section,
                seat_number,
                row_number,
                row_number || CAST(LTRIM(seat_number, 'S')::integer AS TEXT) AS seat_label
            FROM windah_basudatra.seat
            WHERE venue_id = %s
            ORDER BY section, row_number, seat_number
        ''', [event['venue_id']])
        cols  = [c[0] for c in cur.description]
        seats = [dict(zip(cols, r)) for r in cur.fetchall()]

    for seat in seats:
        seat['seat_id'] = str(seat['seat_id'])

    promo_error    = None
    promo_success  = None

    if request.method == 'POST':

        if 'apply_promo' in request.POST:
            promo_code = request.POST.get('promo_code', '').strip()
            with connection.cursor() as cur:
                cur.execute('''
                    SELECT promotion_id, discount_type, discount_value
                    FROM windah_basudatra.promotion
                    WHERE promo_code = %s
                      AND start_date <= CURRENT_DATE
                      AND end_date   >= CURRENT_DATE
                ''', [promo_code])
                promo = cur.fetchone()

            if promo:
                discount_type  = promo[1]
                discount_value = float(promo[2])
                if discount_type == 'PERCENTAGE':
                    promo_success = f'Promo "{promo_code}" valid! Diskon {discount_value:.0f}%.'
                else:
                    promo_success = f'Promo "{promo_code}" valid! Diskon Rp {discount_value:,.0f}.'
            else:
                promo_error = 'Kode promo tidak valid.'

        elif 'place_order' in request.POST:
            messages.success(request, 'Pesanan berhasil dibuat!')
            return redirect('pesanan')

    context = {
        'event':        event,
        'categories':   categories,
        'seats':        seats,
        'promo_error':  promo_error,
        'promo_success': promo_success,
    }
    return render(request, 'checkout.html', context)  # ← fix path template


@login_required
def order_list(request):

    role = _get_role(request)

    search_query  = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    if role == 'admin' or request.user.is_superuser:
        sql = '''
            SELECT
                o.order_id,
                o.order_date,
                o.payment_status,
                o.total_amount,
                c.full_name AS customer_name
            FROM windah_basudatra."order" o
            JOIN windah_basudatra.customer c ON o.customer_id = c.customer_id
            WHERE 1=1
        '''
        params = []

    elif role == 'organizer':
        sql = '''
            SELECT DISTINCT
                o.order_id,
                o.order_date,
                o.payment_status,
                o.total_amount,
                c.full_name AS customer_name
            FROM windah_basudatra."order" o
            JOIN windah_basudatra.customer c         ON o.customer_id = c.customer_id
            JOIN windah_basudatra.ticket t           ON t.order_id = o.order_id
            JOIN windah_basudatra.ticket_category tc ON tc.category_id = t.category_id
            JOIN windah_basudatra.event e            ON e.event_id = tc.event_id
            JOIN windah_basudatra.organizer org      ON org.organizer_id = e.organizer_id
            JOIN windah_basudatra.user_account u     ON u.user_id = org.user_id
            WHERE u.username = %s
        '''
        params = [request.user.username]

    else:
        # Customer: hanya order miliknya sendiri
        sql = '''
            SELECT
                o.order_id,
                o.order_date,
                o.payment_status,
                o.total_amount,
                c.full_name AS customer_name
            FROM windah_basudatra."order" o
            JOIN windah_basudatra.customer c     ON o.customer_id = c.customer_id
            JOIN windah_basudatra.user_account u ON u.user_id = c.user_id
            WHERE u.username = %s
        '''
        params = [request.user.username]

    if search_query:
        if role in ('admin', 'organizer') or request.user.is_superuser:
            sql += ''' AND (
                CAST(o.order_id AS TEXT) ILIKE %s
                OR c.full_name ILIKE %s
            )'''
            params.append(f'%{search_query}%')
            params.append(f'%{search_query}%')
        else:
            sql += ' AND CAST(o.order_id AS TEXT) ILIKE %s'
            params.append(f'%{search_query}%')

    if status_filter:
        sql += ' AND o.payment_status = %s'
        params.append(status_filter)

    sql += ' ORDER BY o.order_date DESC'

    with connection.cursor() as cur:
        cur.execute(sql, params)
        cols   = [c[0] for c in cur.description]
        orders = [dict(zip(cols, r)) for r in cur.fetchall()]

    for o in orders:
        o['order_id']     = str(o['order_id'])
        o['total_amount'] = float(o['total_amount'])
        o['order_date']   = o['order_date'].strftime('%Y-%m-%d %H:%M') if o['order_date'] else '-'

    total_order   = len(orders)
    total_paid    = sum(1 for o in orders if o['payment_status'] == 'PAID')
    total_pending = sum(1 for o in orders if o['payment_status'] == 'PENDING')
    total_revenue = sum(o['total_amount'] for o in orders if o['payment_status'] == 'PAID')

    # Konversi total_revenue ke integer agar template bisa format dengan floatformat
    total_revenue = int(total_revenue)

    context = {
        'orders':        orders,
        'is_admin':      role == 'admin' or request.user.is_superuser,
        'is_organizer':  role == 'organizer',
        'is_customer':   role == 'customer',
        'search_query':  search_query,
        'status_filter': status_filter,
        'total_order':   total_order,
        'total_paid':    total_paid,
        'total_pending': total_pending,
        'total_revenue': total_revenue,
        'status_choices': [
            ('PAID',    'Lunas'),
            ('PENDING', 'Pending'),
            ('FAILED',  'Gagal'),
        ],
    }
    return render(request, 'order_list.html', context)


@login_required
def order_update(request, order_id):
    """Update payment_status order — hanya Admin."""

    role = _get_role(request)
    if role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Anda tidak memiliki akses untuk mengubah order.')
        return redirect('semua_order')

    # Ambil data order yang akan diupdate
    with connection.cursor() as cur:
        cur.execute('''
            SELECT order_id, payment_status
            FROM windah_basudatra."order"
            WHERE order_id = %s
        ''', [str(order_id)])
        row = cur.fetchone()

    if not row:
        messages.error(request, 'Order tidak ditemukan.')
        return redirect('semua_order')

    order = {
        'order_id':       str(row[0]),
        'payment_status': row[1],
    }

    if request.method == 'POST':
        new_status = request.POST.get('payment_status', '').strip()
        valid_statuses = ['PAID', 'PENDING', 'FAILED']

        if new_status not in valid_statuses:
            messages.error(request, 'Status pembayaran tidak valid.')
        else:
            with connection.cursor() as cur:
                cur.execute('''
                    UPDATE windah_basudatra."order"
                    SET payment_status = %s
                    WHERE order_id = %s
                ''', [new_status, str(order_id)])
            messages.success(request, f'Status order berhasil diperbarui menjadi {new_status}.')
            return redirect('semua_order')

    context = {
        'order':          order,
        'status_choices': [
            ('PAID',    'Lunas'),
            ('PENDING', 'Pending'),
            ('FAILED',  'Gagal'),
        ],
    }
    return render(request, 'order_update.html', context)


@login_required
def order_delete(request, order_id):
    """Hapus order — hanya Admin."""

    role = _get_role(request)
    if role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Anda tidak memiliki akses untuk menghapus order.')
        return redirect('semua_order')

    # Ambil data order untuk konfirmasi
    with connection.cursor() as cur:
        cur.execute('''
            SELECT order_id, payment_status, total_amount
            FROM windah_basudatra."order"
            WHERE order_id = %s
        ''', [str(order_id)])
        row = cur.fetchone()

    if not row:
        messages.error(request, 'Order tidak ditemukan.')
        return redirect('semua_order')

    order = {
        'order_id':       str(row[0]),
        'payment_status': row[1],
        'total_amount':   float(row[2]),
    }

    if request.method == 'POST':
        if 'confirm_delete' in request.POST:
            with connection.cursor() as cur:
                cur.execute('''
                    DELETE FROM windah_basudatra."order"
                    WHERE order_id = %s
                ''', [str(order_id)])
            messages.success(request, 'Order berhasil dihapus.')
        return redirect('semua_order')

    context = {
        'order': order,
    }
    return render(request, 'order_delete.html', context)
@login_required
def promotion_create(request):
    """Buat promo baru — hanya Admin."""
    role = _get_role(request)
    if role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Anda tidak memiliki akses.')
        return redirect('promosi')

    if request.method == 'POST':
        promo_code     = request.POST.get('promo_code', '').strip().upper()
        discount_type  = request.POST.get('discount_type', '').strip()
        discount_value = request.POST.get('discount_value', '').strip()
        start_date     = request.POST.get('start_date', '').strip()
        end_date       = request.POST.get('end_date', '').strip()
        usage_limit    = request.POST.get('usage_limit', '').strip()

        # Validasi
        errors = []
        if not promo_code:
            errors.append('Kode promo wajib diisi.')
        if discount_type not in ('PERCENTAGE', 'NOMINAL'):
            errors.append('Tipe diskon tidak valid.')
        if not discount_value or float(discount_value) <= 0:
            errors.append('Nilai diskon harus lebih dari 0.')
        if not start_date or not end_date:
            errors.append('Tanggal mulai dan berakhir wajib diisi.')
        if start_date and end_date and end_date < start_date:
            errors.append('Tanggal berakhir harus sama atau setelah tanggal mulai.')
        if not usage_limit or int(usage_limit) <= 0:
            errors.append('Batas penggunaan harus lebih dari 0.')

        if not errors:
            # Cek duplikat kode promo
            with connection.cursor() as cur:
                cur.execute('''
                    SELECT COUNT(*) FROM windah_basudatra.promotion
                    WHERE promo_code = %s
                ''', [promo_code])
                if cur.fetchone()[0] > 0:
                    errors.append('Kode promo sudah digunakan.')

        if not errors:
            with connection.cursor() as cur:
                cur.execute('''
                    INSERT INTO windah_basudatra.promotion
                        (promo_code, discount_type, discount_value,
                         start_date, end_date, usage_limit)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', [promo_code, discount_type, float(discount_value),
                      start_date, end_date, int(usage_limit)])
            messages.success(request, f'Promo "{promo_code}" berhasil dibuat.')
            return redirect('promosi')

        for err in errors:
            messages.error(request, err)

    return redirect('promosi')


@login_required
def promotion_update(request, promotion_id):
    """Update data promo — hanya Admin."""
    role = _get_role(request)
    if role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Anda tidak memiliki akses.')
        return redirect('promosi')

    if request.method == 'POST':
        promo_code     = request.POST.get('promo_code', '').strip().upper()
        discount_type  = request.POST.get('discount_type', '').strip()
        discount_value = request.POST.get('discount_value', '').strip()
        start_date     = request.POST.get('start_date', '').strip()
        end_date       = request.POST.get('end_date', '').strip()
        usage_limit    = request.POST.get('usage_limit', '').strip()

        # Validasi
        errors = []
        if not promo_code:
            errors.append('Kode promo wajib diisi.')
        if discount_type not in ('PERCENTAGE', 'NOMINAL'):
            errors.append('Tipe diskon tidak valid.')
        if not discount_value or float(discount_value) <= 0:
            errors.append('Nilai diskon harus lebih dari 0.')
        if not start_date or not end_date:
            errors.append('Tanggal mulai dan berakhir wajib diisi.')
        if start_date and end_date and end_date < start_date:
            errors.append('Tanggal berakhir harus sama atau setelah tanggal mulai.')
        if not usage_limit or int(usage_limit) <= 0:
            errors.append('Batas penggunaan harus lebih dari 0.')

        if not errors:
            # Cek duplikat kode promo (kecuali milik sendiri)
            with connection.cursor() as cur:
                cur.execute('''
                    SELECT COUNT(*) FROM windah_basudatra.promotion
                    WHERE promo_code = %s AND promotion_id != %s
                ''', [promo_code, str(promotion_id)])
                if cur.fetchone()[0] > 0:
                    errors.append('Kode promo sudah digunakan.')

        if not errors:
            with connection.cursor() as cur:
                cur.execute('''
                    UPDATE windah_basudatra.promotion
                    SET promo_code     = %s,
                        discount_type  = %s,
                        discount_value = %s,
                        start_date     = %s,
                        end_date       = %s,
                        usage_limit    = %s
                    WHERE promotion_id = %s
                ''', [promo_code, discount_type, float(discount_value),
                      start_date, end_date, int(usage_limit),
                      str(promotion_id)])
            messages.success(request, f'Promo "{promo_code}" berhasil diperbarui.')
            return redirect('promosi')

        for err in errors:
            messages.error(request, err)

    return redirect('promosi')


@login_required
def promotion_delete(request, promotion_id):
    """Hapus promo — hanya Admin."""
    role = _get_role(request)
    if role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Anda tidak memiliki akses.')
        return redirect('promosi')

    if request.method == 'POST':
        if 'confirm_delete' in request.POST:
            with connection.cursor() as cur:
                cur.execute('''
                    DELETE FROM windah_basudatra.promotion
                    WHERE promotion_id = %s
                ''', [str(promotion_id)])
            messages.success(request, 'Promo berhasil dihapus.')

    return redirect('promosi')

@login_required
def promotion_list(request):
    """Daftar promosi — semua role bisa lihat, hanya Admin yang bisa CUD."""

    role = _get_role(request)

    search_query = request.GET.get('q', '').strip()
    type_filter  = request.GET.get('type', '').strip()

    sql = '''
        SELECT
            p.promotion_id,
            p.promo_code,
            p.discount_type,
            p.discount_value,
            p.start_date,
            p.end_date,
            p.usage_limit,
            COUNT(op.order_promotion_id) AS used_count
        FROM windah_basudatra.promotion p
        LEFT JOIN windah_basudatra.order_promotion op
               ON op.promotion_id = p.promotion_id
        WHERE 1=1
    '''
    params = []

    if search_query:
        sql += ' AND p.promo_code ILIKE %s'
        params.append(f'%{search_query}%')

    if type_filter:
        sql += ' AND p.discount_type = %s'
        params.append(type_filter)

    sql += ' GROUP BY p.promotion_id ORDER BY p.promo_code ASC'

    with connection.cursor() as cur:
        cur.execute(sql, params)
        cols       = [c[0] for c in cur.description]
        promotions = [dict(zip(cols, r)) for r in cur.fetchall()]

    for p in promotions:
        p['promotion_id']   = str(p['promotion_id'])
        p['discount_value'] = float(p['discount_value'])
        p['start_date']     = str(p['start_date'])
        p['end_date']       = str(p['end_date'])

    total_promo      = len(promotions)
    total_usage      = sum(p['used_count'] for p in promotions)
    total_percentage = sum(1 for p in promotions if p['discount_type'] == 'PERCENTAGE')

    context = {
        'promotions':      promotions,
        'is_admin':        role == 'admin' or request.user.is_superuser,
        'search_query':    search_query,
        'type_filter':     type_filter,
        'total_promo':     total_promo,
        'total_usage':     total_usage,
        'total_percentage': total_percentage,
    }
    return render(request, 'promotion_list.html', context)