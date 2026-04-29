import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.db import connection
from django.views.decorators.http import require_POST, require_GET


# ── HELPER ──────────────────────────────────────────────────────────────────

def _get_role(request):
    role = request.GET.get('role', 'user')
    if role not in ('admin', 'organizer', 'user'):
        role = 'user'
    return role

def _can_manage(role):
    return role in ('admin', 'organizer')

def _format_rp(n):
    return f"Rp {n:,.0f}".replace(',', '.')


# ── VIEWS ────────────────────────────────────────────────────────────────────

@require_GET
def ticket_category_list(request):
    role = _get_role(request)

    with connection.cursor() as cur:
        # Ambil semua kategori tiket beserta nama acara
        cur.execute("""
            SELECT
                tk.id,
                tk.kategori,
                a.nama    AS acara,
                tk.harga,
                tk.kuota
            FROM ticket_kategori tk
            JOIN acara a ON a.id = tk.acara_id
            ORDER BY a.nama, tk.kategori
        """)
        columns = [col[0] for col in cur.description]
        tickets = [dict(zip(columns, row)) for row in cur.fetchall()]

        # Ambil daftar acara buat dropdown filter & form
        cur.execute("SELECT nama FROM acara ORDER BY nama")
        acara_list = [row[0] for row in cur.fetchall()]

    total_kuota     = sum(t['kuota'] for t in tickets)
    max_harga       = max((t['harga'] for t in tickets), default=0)

    # Konversi Decimal ke int/float supaya json.dumps happy
    tickets_serializable = [
        {**t, 'harga': int(t['harga']), 'kuota': int(t['kuota'])}
        for t in tickets
    ]

    context = {
        'tickets':          tickets,
        'tickets_json':     json.dumps(tickets_serializable),
        'acara_list_json':  json.dumps(acara_list),
        'total_kuota':      f"{total_kuota:,}".replace(',', '.'),
        'harga_tertinggi':  _format_rp(max_harga),
        'can_manage':       _can_manage(role),
        'role':             role,
    }
    return render(request, 'ticket_category/ticket_category.html', context)


@require_POST
def ticket_category_create(request):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect(f'/ticket-category/?role={role}')

    acara_nama = request.POST.get('acara', '').strip()
    kategori   = request.POST.get('kategori', '').strip()
    harga      = request.POST.get('harga', 0)
    kuota      = request.POST.get('kuota', 0)

    if acara_nama and kategori:
        with connection.cursor() as cur:
            # Cari acara_id dulu
            cur.execute("SELECT id FROM acara WHERE nama = %s", [acara_nama])
            row = cur.fetchone()
            if row:
                acara_id = row[0]
                cur.execute(
                    "INSERT INTO ticket_kategori (acara_id, kategori, harga, kuota) VALUES (%s, %s, %s, %s)",
                    [acara_id, kategori, harga, kuota]
                )

    return redirect(f'/ticket-category/?role={role}')


@require_GET
def ticket_category_data(request, pk):
    """Endpoint JSON buat JS fetch waktu openEdit()"""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT tk.id, tk.kategori, a.nama AS acara, tk.harga, tk.kuota
            FROM ticket_kategori tk
            JOIN acara a ON a.id = tk.acara_id
            WHERE tk.id = %s
        """, [pk])
        row = cur.fetchone()

    if not row:
        raise Http404

    return JsonResponse({
        'id': row[0], 'kategori': row[1], 'acara': row[2],
        'harga': int(row[3]), 'kuota': int(row[4])
    })


@require_POST
def ticket_category_edit(request, pk):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect(f'/ticket-category/?role={role}')

    acara_nama = request.POST.get('acara', '').strip()
    kategori   = request.POST.get('kategori', '').strip()
    harga      = request.POST.get('harga', 0)
    kuota      = request.POST.get('kuota', 0)

    if acara_nama and kategori:
        with connection.cursor() as cur:
            cur.execute("SELECT id FROM acara WHERE nama = %s", [acara_nama])
            row = cur.fetchone()
            if row:
                acara_id = row[0]
                cur.execute("""
                    UPDATE ticket_kategori
                    SET acara_id = %s, kategori = %s, harga = %s, kuota = %s
                    WHERE id = %s
                """, [acara_id, kategori, harga, kuota, pk])

    return redirect(f'/ticket-category/?role={role}')


@require_POST
def ticket_category_delete(request, pk):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect(f'/ticket-category/?role={role}')

    with connection.cursor() as cur:
        cur.execute("DELETE FROM ticket_kategori WHERE id = %s", [pk])

    return redirect(f'/ticket-category/?role={role}')
