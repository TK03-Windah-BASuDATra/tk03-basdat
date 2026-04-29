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

    # Ambil data event + artis
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

    # Ambil artis event ini
    with connection.cursor() as cur:
        cur.execute('''
            SELECT a.name
            FROM windah_basudatra.artist a
            JOIN windah_basudatra.event_artist ea ON a.artist_id = ea.artist_id
            WHERE ea.event_id = %s
            ORDER BY ea.role
        ''', [str(event_id)])
        event['artists'] = [r[0] for r in cur.fetchall()]

    # Ambil kategori tiket
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

    # Konversi price ke float agar bisa di-serialize ke JSON di template
    for cat in categories:
        cat['category_id'] = str(cat['category_id'])
        cat['price']       = float(cat['price'])

    # Ambil kursi venue ini
    with connection.cursor() as cur:
        cur.execute('''
            SELECT
                seat_id,
                section,
                seat_number,
                row_number
            FROM windah_basudatra.seat
            WHERE venue_id = %s
            ORDER BY section, row_number, seat_number
        ''', [event['venue_id']])
        cols  = [c[0] for c in cur.description]
        seats = [dict(zip(cols, r)) for r in cur.fetchall()]

    for seat in seats:
        seat['seat_id'] = str(seat['seat_id'])

    promo_error   = None
    promo_success = None
    promo_discount = 0

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
        'event':         event,
        'categories':    categories,
        'seats':         seats,
        'promo_error':   promo_error,
        'promo_success': promo_success,
    }
    return render(request, 'checkout.html', context)


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
        sql = '''
            SELECT
                o.order_id,
                o.order_date,
                o.payment_status,
                o.total_amount,
                c.full_name AS customer_name
            FROM windah_basudatra."order" o
            JOIN windah_basudatra.customer c    ON o.customer_id = c.customer_id
            JOIN windah_basudatra.user_account u ON u.user_id = c.user_id
            WHERE u.username = %s
        '''
        params = [request.user.username]

    if search_query:
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

    # Konversi tipe data
    for o in orders:
        o['order_id']     = str(o['order_id'])
        o['total_amount'] = float(o['total_amount'])
        o['order_date']   = o['order_date'].strftime('%Y-%m-%d %H:%M') if o['order_date'] else '-'

    total_order   = len(orders)
    total_paid    = sum(1 for o in orders if o['payment_status'] == 'PAID')
    total_pending = sum(1 for o in orders if o['payment_status'] == 'PENDING')
    total_revenue = sum(o['total_amount'] for o in orders if o['payment_status'] == 'PAID')

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
    return render(request, 'orders/order_list.html', context)