import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_POST, require_GET

def _get_role(request):
    role = request.session.get('role')
    if role not in ('admin', 'organizer', 'customer'):
        role = 'guest'
    return role

def _can_manage(role):
    return role == 'admin'

def validate_artist(nama, genre):
    errors = {}
    nama = (nama or "").strip()
    genre = (genre or "").strip()
    if not nama:
        errors["nama"] = "Nama artis wajib diisi."
    elif len(nama) > 100:
        errors["nama"] = "Nama artis terlalu panjang."
    if genre and len(genre) > 50:
        errors["genre"] = "Genre terlalu panjang."
    return errors

def _get_artist_list_context(role):
    with connection.cursor() as cur:
        cur.execute('''
            SELECT a.artist_id as id, a.name as nama, a.genre,
                COUNT(ea.event_id) as tampil
            FROM windah_basudatra.artist a
            LEFT JOIN windah_basudatra.event_artist ea ON a.artist_id = ea.artist_id
            GROUP BY a.artist_id, a.name, a.genre
            ORDER BY a.name ASC
        ''')
        columns = [col[0] for col in cur.description]
        artists = [dict(zip(columns, row)) for row in cur.fetchall()]

        cur.execute('''
            SELECT event_id, event_title
            FROM windah_basudatra.event
            ORDER BY event_title ASC
        ''')
        events = [{'id': str(r[0]), 'title': r[1]} for r in cur.fetchall()]

    genres = {a['genre'] for a in artists if a['genre'] and a['genre'] != 'Lainnya'}

    return {
        'artists': artists,
        'artists_json': json.dumps(artists, default=str),
        'events_json': json.dumps(events),
        'total_genre': len(genres),
        'total_tampil': sum(a['tampil'] for a in artists),
        'can_manage': _can_manage(role),
    }

@require_GET
def artist_list(request):
    role = _get_role(request)
    return render(request, 'artist.html', _get_artist_list_context(role))

@require_GET
def add_to_event_page(request):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect('/artist/')
    return render(request, 'add_to_event.html')

@require_POST
def artist_add_to_event(request):
    role = _get_role(request)
    if not _can_manage(role):
        return JsonResponse({'ok': False, 'error': 'Akses ditolak.'}, status=403)

    artist_id = request.POST.get('artist_id', '').strip()
    event_id  = request.POST.get('event_id', '').strip()
    role_name = request.POST.get('role_artist', '').strip()

    try:
        with connection.cursor() as cur:
            cur.execute('''
                INSERT INTO windah_basudatra.event_artist (event_id, artist_id, role)
                VALUES (%s, %s, %s)
            ''', [event_id, artist_id, role_name or None])
        return JsonResponse({'ok': True})

    except Exception as exc:
        raw = str(exc).split('\n')[0].strip()
        if 'ERROR:' in raw:
            raw = raw[raw.index('ERROR:') + len('ERROR:'):].strip()
        return JsonResponse({'ok': False, 'error': raw})

@require_POST
def artist_create(request):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect('/artist/')

    nama = request.POST.get('nama')
    genre = request.POST.get('genre') or 'Lainnya'
    errors = validate_artist(nama, genre)

    if not errors:
        with connection.cursor() as cur:
            cur.execute('''
                INSERT INTO windah_basudatra.artist (name, genre)
                VALUES (%s, %s)
            ''', [nama, genre])
        return redirect('/artist/?success=created')

    return redirect('/artist/')

@require_GET
def artist_data(request, pk):
    with connection.cursor() as cur:
        cur.execute('''
            SELECT artist_id as id, name as nama, genre
            FROM windah_basudatra.artist
            WHERE artist_id = %s
        ''', [pk])
        row = cur.fetchone()
        if not row:
            return JsonResponse({'error': 'Not found'}, status=404)
        return JsonResponse({'id': str(row[0]), 'nama': row[1], 'genre': row[2]})

@require_POST
def artist_edit(request, pk):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect('/artist/')

    nama = request.POST.get('nama')
    genre = request.POST.get('genre') or 'Lainnya'
    errors = validate_artist(nama, genre)

    if not errors:
        with connection.cursor() as cur:
            cur.execute('''
                UPDATE windah_basudatra.artist
                SET name = %s, genre = %s
                WHERE artist_id = %s
            ''', [nama, genre, pk])
        return redirect('/artist/?success=updated')

    return redirect('/artist/')

@require_POST
def artist_delete(request, pk):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect('/artist/')

    with connection.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM windah_basudatra.event_artist WHERE artist_id = %s', [pk])
        if cur.fetchone()[0] == 0:
            cur.execute('DELETE FROM windah_basudatra.artist WHERE artist_id = %s', [pk])
            return redirect('/artist/?success=deleted')
        else:
            return redirect('/artist/?error=has_events')