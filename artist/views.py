import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.db import connection
from django.views.decorators.http import require_POST, require_GET

def _get_role(request):
    """Mengambil role dari query parameter, default ke 'customer'."""
    role = request.GET.get('role', 'customer')
    if role not in ('admin', 'organizer', 'customer'):
        role = 'customer'
    return role

def _can_manage(role):
    """Hanya Admin yang punya akses CRUD Artist sesuai spesifikasi."""
    return role == 'admin'

def validate_artist(nama, genre):
    """Validasi input artist."""
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

@require_GET
def artist_list(request):
    role = _get_role(request)
    
    with connection.cursor() as cur:
        # Query untuk mengambil data artis sekaligus jumlah event yang diikuti
        cur.execute('''
            SELECT 
                a.artist_id as id, 
                a.name as nama, 
                a.genre, 
                COUNT(ea.event_id) as tampil
            FROM windah_basudatra.artist a
            LEFT JOIN windah_basudatra.event_artist ea ON a.artist_id = ea.artist_id
            GROUP BY a.artist_id, a.name, a.genre
            ORDER BY a.name ASC
        ''')
        
        columns = [col[0] for col in cur.description]
        artists = [dict(zip(columns, row)) for row in cur.fetchall()]

    # Hitung statistik untuk Stat Cards
    genres = {a['genre'] for a in artists if a['genre'] and a['genre'] != 'Lainnya'}
    total_tampil = sum(a['tampil'] for a in artists)

    context = {
        'artists': artists,
        'artists_json': json.dumps(artists, default=str), # Data untuk diolah artist.js
        'total_genre': len(genres),
        'total_tampil': total_tampil,
        'can_manage': _can_manage(role),
        'role': role,
    }
    return render(request, 'artist/artist.html', context)

@require_POST
def artist_create(request):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect(f'/artist/?role={role}')

    nama = request.POST.get('nama')
    genre = request.POST.get('genre') or 'Lainnya'
    errors = validate_artist(nama, genre)

    if not errors:
        with connection.cursor() as cur:
            cur.execute('''
                INSERT INTO windah_basudatra.artist (name, genre)
                VALUES (%s, %s)
            ''', [nama, genre])

    return redirect(f'/artist/?role={role}')

@require_GET
def artist_data(request, pk):
    """Endpoint JSON untuk mengisi data di Modal Edit."""
    with connection.cursor() as cur:
        cur.execute('''
            SELECT artist_id as id, name as nama, genre 
            FROM windah_basudatra.artist 
            WHERE artist_id = %s
        ''', [pk])
        row = cur.fetchone()
        if not row:
            return JsonResponse({'error': 'Not found'}, status=404)
        
        return JsonResponse({
            'id': str(row[0]),
            'nama': row[1],
            'genre': row[2]
        })

@require_POST
def artist_edit(request, pk):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect(f'/artist/?role={role}')

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

    return redirect(f'/artist/?role={role}')

@require_POST
def artist_delete(request, pk):
    role = _get_role(request)
    if not _can_manage(role):
        return redirect(f'/artist/?role={role}')

    with connection.cursor() as cur:
        # Proteksi: Cek apakah artis sedang dipakai di event_artist
        cur.execute('SELECT COUNT(*) FROM windah_basudatra.event_artist WHERE artist_id = %s', [pk])
        if cur.fetchone()[0] == 0:
            cur.execute('DELETE FROM windah_basudatra.artist WHERE artist_id = %s', [pk])

    return redirect(f'/artist/?role={role}')