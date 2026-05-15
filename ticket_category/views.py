import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.db import connection
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET


def _get_role(request):
    role = request.session.get('role')
    if role not in ('admin', 'organizer', 'customer'):
        role = 'guest'
    return role

def _can_manage(role):
    return role in ('admin', 'organizer')

def _format_rp(n):
    return f"Rp {n:,.0f}".replace(',', '.')


@require_GET
def ticket_category_list(request):
    role = _get_role(request)
    event_id_filter = request.GET.get('event_id', '').strip()
    event_id_error = None

    with connection.cursor() as cur:
        if event_id_filter:
            try:
                cur.execute("SELECT * FROM get_ticket_availability(%s)", [event_id_filter])
                columns = [col[0] for col in cur.description]
                tickets = [dict(zip(columns, row)) for row in cur.fetchall()]
                tickets = [
                    {
                        'category_id': t['category_id'],
                        'category_name': t['category_name'],
                        'acara': '',
                        'price': t['price'],
                        'quota': int(t['sisa_kuota']),
                    }
                    for t in tickets
                ]
                cur.execute("SELECT event_title FROM event WHERE event_id = %s", [event_id_filter])
                row = cur.fetchone()
                acara_nama = row[0] if row else ''
                for t in tickets:
                    t['acara'] = acara_nama
            except Exception as exc:
                msg = str(exc).split('\n')[0].strip()
                event_id_error = msg
                tickets = []
        else:
            cur.execute("""
                SELECT
                    tc.category_id,
                    tc.category_name,
                    e.event_title AS acara,
                    tc.price,
                    tc.quota - COUNT(t.ticket_id) AS quota
                FROM ticket_category tc
                JOIN event e ON e.event_id = tc.event_id
                LEFT JOIN ticket t ON t.category_id = tc.category_id
                GROUP BY tc.category_id, tc.category_name, e.event_title, tc.price, tc.quota
                ORDER BY e.event_title, tc.category_name
            """)
            columns = [col[0] for col in cur.description]
            tickets = [dict(zip(columns, row)) for row in cur.fetchall()]

        cur.execute("SELECT event_id, event_title FROM event ORDER BY event_title")
        acara_list = [{'id': str(row[0]), 'nama': row[1]} for row in cur.fetchall()]

    total_kuota = sum(t['quota'] for t in tickets)
    max_harga = max((t['price'] for t in tickets), default=0)

    tickets_serializable = [
        {
            'id': str(t['category_id']),
            'kategori': t['category_name'],
            'acara': t['acara'],
            'harga': int(t['price']),
            'kuota': int(t['quota']),
        }
        for t in tickets
    ]

    context = {
        'tickets': tickets,
        'tickets_json': json.dumps(tickets_serializable),
        'acara_list_json': json.dumps([{'id': a['id'], 'nama': a['nama']} for a in acara_list]),
        'total_kuota': f"{total_kuota:,}".replace(',', '.'),
        'harga_tertinggi': _format_rp(max_harga),
        'can_manage': _can_manage(role),
        'role': role,
        'event_id_filter': event_id_filter,
        'event_id_error': event_id_error,
    }
    return render(request, 'ticket_category.html', context)


@require_POST
def ticket_category_create(request):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect('/ticket-category/')

    event_id      = request.POST.get('event_id', '').strip()
    category_name = request.POST.get('kategori', '').strip()
    price         = request.POST.get('harga', 0)
    quota         = request.POST.get('kuota', 0)

    if event_id and category_name:
        with connection.cursor() as cur:
            cur.execute(
                "INSERT INTO ticket_category (event_id, category_name, price, quota) VALUES (%s, %s, %s, %s)",
                [event_id, category_name, price, quota]
            )
        messages.success(request, 'Kategori tiket berhasil ditambahkan.')

    return redirect('/ticket-category/')


@require_GET
def ticket_category_data(request, pk):
    with connection.cursor() as cur:
        cur.execute("""
            SELECT tc.category_id, tc.category_name, e.event_title, e.event_id, tc.price, tc.quota
            FROM ticket_category tc
            JOIN event e ON e.event_id = tc.event_id
            WHERE tc.category_id = %s
        """, [pk])
        row = cur.fetchone()

    if not row:
        raise Http404

    return JsonResponse({
        'id':       str(row[0]),
        'kategori': row[1],
        'acara':    row[2],
        'event_id': str(row[3]),
        'harga':    int(row[4]),
        'kuota':    int(row[5]),
    })


@require_POST
def ticket_category_edit(request, pk):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect('/ticket-category/')

    event_id      = request.POST.get('event_id', '').strip()
    category_name = request.POST.get('kategori', '').strip()
    price         = request.POST.get('harga', 0)
    quota         = request.POST.get('kuota', 0)

    if event_id and category_name:
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE ticket_category
                SET event_id = %s, category_name = %s, price = %s, quota = %s
                WHERE category_id = %s
            """, [event_id, category_name, price, quota, pk])
        messages.success(request, 'Kategori tiket berhasil diperbarui.')

    return redirect('/ticket-category/')


@require_POST
def ticket_category_delete(request, pk):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect('/ticket-category/')

    with connection.cursor() as cur:
        cur.execute("DELETE FROM ticket_category WHERE category_id = %s", [pk])
    messages.success(request, 'Kategori tiket berhasil dihapus.')

    return redirect('/ticket-category/')