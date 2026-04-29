import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.db import connection
from django.views.decorators.http import require_POST, require_GET


def _get_role(request):
    role = request.GET.get('role', 'customer')
    if role not in ('admin', 'organizer', 'customer'):
        role = 'customer'
    return role

def _can_manage(role):
    return role in ('admin', 'organizer')

def _format_rp(n):
    return f"Rp {n:,.0f}".replace(',', '.')


@require_GET
def ticket_category_list(request):
    role = _get_role(request)

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                tc.category_id,
                tc.category_name,
                e.event_title   AS acara,
                tc.price,
                tc.quota
            FROM ticket_category tc
            JOIN event e ON e.event_id = tc.event_id
            ORDER BY e.event_title, tc.category_name
        """)
        columns = [col[0] for col in cur.description]
        tickets = [dict(zip(columns, row)) for row in cur.fetchall()]

        cur.execute("SELECT event_id, event_title FROM event ORDER BY event_title")
        acara_list = [{'id': str(row[0]), 'nama': row[1]} for row in cur.fetchall()]

    total_kuota = sum(t['quota'] for t in tickets)
    max_harga   = max((t['price'] for t in tickets), default=0)

    tickets_serializable = [
        {
            'id':       str(t['category_id']),
            'kategori': t['category_name'],
            'acara':    t['acara'],
            'harga':    int(t['price']),
            'kuota':    int(t['quota']),
        }
        for t in tickets
    ]

    acara_list_serializable = [
        {'id': a['id'], 'nama': a['nama']} for a in acara_list
    ]

    context = {
        'tickets':          tickets,
        'tickets_json':     json.dumps(tickets_serializable),
        'acara_list_json':  json.dumps(acara_list_serializable),
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

    return redirect(f'/ticket-category/?role={role}')


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
        return redirect(f'/ticket-category/?role={role}')

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

    return redirect(f'/ticket-category/?role={role}')


@require_POST
def ticket_category_delete(request, pk):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect(f'/ticket-category/?role={role}')

    with connection.cursor() as cur:
        cur.execute("DELETE FROM ticket_category WHERE category_id = %s", [pk])

    return redirect(f'/ticket-category/?role={role}')