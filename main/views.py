from django.urls import path
from . import views
from django.db import connection
from datetime import date

def _format_omzet(n):
    if n >= 1_000_000:
        return f"Rp {n/1_000_000:.1f}M"
    return f"Rp {n:,.0f}".replace(',', '.')

def dashboard(request):
    role = request.GET.get('role', 'guest')
    if role not in ('admin', 'organizer', 'customer'):
        role = 'guest'

    if role == 'admin':
        context = dashboard_admin(request)
    elif role == 'organizer':
        context = dashboard_organizer(request)
    elif role == 'customer':
        context = dashboard_customer(request)
    else:
        context = dashboard_guest(request)

    return render(request, 'dashboard/dashboard.html', context)

def dashboard_admin(request):
    today = date.today()
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM user_account")
        total_pengguna = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM event
            WHERE DATE_TRUNC('month', event_datetime) = DATE_TRUNC('month', CURRENT_DATE)
        """)
        total_acara = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(SUM(total_amount),0) FROM \"order\" WHERE payment_status='PAID'")
        omzet = _format_omzet(cur.fetchone()[0])

        cur.execute("SELECT COUNT(*) FROM promotion WHERE %s BETWEEN start_date AND end_date", [today])
        promosi_aktif = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM venue")
        total_venue = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT venue_id) FROM seat")
        venue_reserved = cur.fetchone()[0]

        cur.execute("SELECT MAX(capacity) FROM venue")
        kapasitas_terbesar = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT COUNT(*) FROM promotion
            WHERE discount_type='PERCENTAGE' AND %s BETWEEN start_date AND end_date
        """, [today])
        promo_persentase = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM promotion
            WHERE discount_type='NOMINAL' AND %s BETWEEN start_date AND end_date
        """, [today])
        promo_nominal = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM order_promotion")
        total_penggunaan_promo = cur.fetchone()[0]

    return {
        'total_pengguna': f"{total_pengguna:,}".replace(',', '.'),
        'total_acara': total_acara,
        'omzet': omzet,
        'promosi_aktif': promosi_aktif,
        'total_venue': total_venue,
        'venue_reserved': venue_reserved,
        'kapasitas_terbesar': f"{kapasitas_terbesar:,}".replace(',', '.'),
        'promo_persentase': promo_persentase,
        'promo_nominal': promo_nominal,
        'total_penggunaan_promo': total_penggunaan_promo,
    }

def dashboard_organizer(request):
    # sementara pakai organizer pertama karena belum ada session
    organizer_id = request.GET.get('organizer_id', '30000000-0000-0000-0000-000000000001')

    with connection.cursor() as cur:
        cur.execute("SELECT organizer_name FROM organizer WHERE organizer_id = %s", [organizer_id])
        row = cur.fetchone()
        organizer_name = row[0] if row else 'Penyelenggara'

        cur.execute("SELECT COUNT(*) FROM event WHERE organizer_id = %s", [organizer_id])
        acara_aktif = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(t.ticket_id)
            FROM ticket t
            JOIN ticket_category tc ON t.category_id = tc.category_id
            JOIN event e ON tc.event_id = e.event_id
            WHERE e.organizer_id = %s
        """, [organizer_id])
        tiket_terjual = cur.fetchone()[0]

        cur.execute("""
            SELECT COALESCE(SUM(o.total_amount), 0)
            FROM "order" o
            JOIN ticket t ON t.order_id = o.order_id
            JOIN ticket_category tc ON t.category_id = tc.category_id
            JOIN event e ON tc.event_id = e.event_id
            WHERE e.organizer_id = %s
              AND o.payment_status = 'PAID'
              AND DATE_TRUNC('month', o.order_date) = DATE_TRUNC('month', CURRENT_DATE)
        """, [organizer_id])
        revenue = _format_omzet(cur.fetchone()[0])

        cur.execute("""
            SELECT COUNT(DISTINCT e.venue_id)
            FROM event e WHERE e.organizer_id = %s
        """, [organizer_id])
        venue_mitra = cur.fetchone()[0]

        cur.execute("""
            SELECT
                e.event_id,
                e.event_title,
                v.venue_name,
                COUNT(t.ticket_id) AS terjual,
                COALESCE(SUM(tc.quota), 0) AS total_kuota
            FROM event e
            JOIN venue v ON e.venue_id = v.venue_id
            JOIN ticket_category tc ON tc.event_id = e.event_id
            LEFT JOIN ticket t ON t.category_id = tc.category_id
            WHERE e.organizer_id = %s
            GROUP BY e.event_id, e.event_title, v.venue_name
            ORDER BY e.event_datetime
        """, [organizer_id])
        cols = [c[0] for c in cur.description]
        events_raw = [dict(zip(cols, r)) for r in cur.fetchall()]

    for ev in events_raw:
        total = ev['total_kuota'] or 1
        ev['persen_terjual'] = round(ev['terjual'] / total * 100)

    return {
        'organizer_name': organizer_name,
        'acara_aktif': acara_aktif,
        'tiket_terjual': f"{tiket_terjual:,}".replace(',', '.'),
        'revenue': revenue,
        'venue_mitra': venue_mitra,
        'events_organizer': events_raw,
    }

def dashboard_customer(request):
    # sementara pakai customer pertama karena belum ada session
    customer_id = request.GET.get('customer_id', '20000000-0000-0000-0000-000000000001')
    today = date.today()

    with connection.cursor() as cur:
        cur.execute("SELECT full_name FROM customer WHERE customer_id = %s", [customer_id])
        row = cur.fetchone()
        customer_name = row[0] if row else 'Customer'

        cur.execute("""
            SELECT COUNT(DISTINCT e.event_id)
            FROM event e
            WHERE e.event_datetime > NOW()
        """)
        upcoming_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(t.ticket_id)
            FROM ticket t
            JOIN "order" o ON t.order_id = o.order_id
            JOIN ticket_category tc ON t.category_id = tc.category_id
            JOIN event e ON tc.event_id = e.event_id
            WHERE o.customer_id = %s
              AND o.payment_status = 'PAID'
              AND e.event_datetime > NOW()
        """, [customer_id])
        tiket_aktif = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(DISTINCT tc.event_id)
            FROM ticket t
            JOIN "order" o ON t.order_id = o.order_id
            JOIN ticket_category tc ON t.category_id = tc.category_id
            WHERE o.customer_id = %s AND o.payment_status = 'PAID'
        """, [customer_id])
        acara_diikuti = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM promotion
            WHERE %s BETWEEN start_date AND end_date
        """, [today])
        kode_promo = cur.fetchone()[0]

        cur.execute("""
            SELECT COALESCE(SUM(total_amount), 0) FROM "order"
            WHERE customer_id = %s
              AND payment_status = 'PAID'
              AND DATE_TRUNC('month', order_date) = DATE_TRUNC('month', CURRENT_DATE)
        """, [customer_id])
        total_belanja = _format_omzet(cur.fetchone()[0])

        cur.execute("""
            SELECT e.event_title, v.venue_name, e.event_datetime, tc.category_name
            FROM ticket t
            JOIN "order" o ON t.order_id = o.order_id
            JOIN ticket_category tc ON t.category_id = tc.category_id
            JOIN event e ON tc.event_id = e.event_id
            JOIN venue v ON e.venue_id = v.venue_id
            WHERE o.customer_id = %s
              AND o.payment_status = 'PAID'
              AND e.event_datetime > NOW()
            ORDER BY e.event_datetime
            LIMIT 5
        """, [customer_id])
        cols = [c[0] for c in cur.description]
        tiket_mendatang = [dict(zip(cols, r)) for r in cur.fetchall()]

    return {
        'customer_name': customer_name,
        'upcoming_count': upcoming_count,
        'tiket_aktif': tiket_aktif,
        'acara_diikuti': acara_diikuti,
        'kode_promo': kode_promo,
        'total_belanja': total_belanja,
        'tiket_mendatang': tiket_mendatang,
    }



def dashboard_guest(request):
    today = date.today()
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM event WHERE event_datetime > NOW()")
        total_acara = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM artist")
        total_artis = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM venue")
        total_venue = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM promotion WHERE %s BETWEEN start_date AND end_date", [today])
        promosi_aktif = cur.fetchone()[0]

        cur.execute("""
            SELECT e.event_title, e.event_datetime, v.venue_name
            FROM event e
            JOIN venue v ON e.venue_id = v.venue_id
            WHERE e.event_datetime > NOW()
            ORDER BY e.event_datetime
            LIMIT 5
        """)
        cols = [c[0] for c in cur.description]
        upcoming_events = [dict(zip(cols, r)) for r in cur.fetchall()]

    return {
        'total_acara': total_acara,
        'total_artis': total_artis,
        'total_venue': total_venue,
        'promosi_aktif': promosi_aktif,
        'upcoming_events': upcoming_events,
    }


def _render_placeholder(request, title, description):
    return _render_placeholder(request, "placeholder_page.html", {
        "page_title": title,
        "page_description": description,
    })


def profile(request):
    return _render_placeholder(
        request,
        "Profile",
        "Halaman profile masih berupa placeholder untuk TK03."
    )


def manajemen_kursi(request):
    return _render_placeholder(
        request,
        "Manajemen Kursi",
        "Halaman manajemen kursi masih berupa placeholder untuk TK03."
    )


def kategori_tiket(request):
    return _render_placeholder(
        request,
        "Kategori Tiket",
        "Halaman kategori tiket masih berupa placeholder untuk TK03."
    )


def manajemen_tiket(request):
    return _render_placeholder(
        request,
        "Manajemen Tiket",
        "Halaman manajemen tiket masih berupa placeholder untuk TK03."
    )


def semua_order(request):
    return _render_placeholder(
        request,
        "Semua Order",
        "Halaman semua order masih berupa placeholder untuk TK03."
    )


def tiket_aset(request):
    return _render_placeholder(
        request,
        "Tiket (Aset)",
        "Halaman tiket aset masih berupa placeholder untuk TK03."
    )


def order_aset(request):
    return _render_placeholder(
        request,
        "Order (Aset)",
        "Halaman order aset masih berupa placeholder untuk TK03."
    )


def tiket_saya(request):
    return _render_placeholder(
        request,
        "Tiket Saya",
        "Halaman tiket saya masih berupa placeholder untuk TK03."
    )


def pesanan(request):
    return _render_placeholder(
        request,
        "Pesanan",
        "Halaman pesanan masih berupa placeholder untuk TK03."
    )


def promosi(request):
    return _render_placeholder(
        request,
        "Promosi",
        "Halaman promosi masih berupa placeholder untuk TK03."
    )


def artis(request):
    return _render_placeholder(
        request,
        "Artis",
        "Halaman artis masih berupa placeholder untuk TK03."
    )


def manajemen_venue(request):
    return redirect("venue_list")


def event_saya(request):
    return redirect("event_manage_list")


def cari_event(request):
    return redirect("event_list")

def venue(request):
    return redirect("venue_list")

