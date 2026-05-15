from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, transaction
import uuid

def _get_role(request):
    role = request.GET.get("role") or request.POST.get("role") or "guest"
    return role if role in ["guest", "admin", "organizer", "customer"] else "guest"

def _get_username(request):
    return request.GET.get("username") or request.POST.get("username") or request.session.get("username", "")

def _require_non_guest(request):
    role = _get_role(request)
    username = _get_username(request)
    if role == "guest":
        messages.error(request, "Silakan login terlebih dahulu.")
        return None, None, redirect(f"/?role=guest")
    return role, username, None

def _dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def manajemen_kursi(request):
    role, username, redirect_response = _require_non_guest(request)
    if redirect_response:
        return redirect_response

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                s.seat_id,
                s.section,
                s.row_number as row,
                s.seat_number as number,
                v.venue_name as venue,
                v.venue_id,
                CASE WHEN hr.seat_id IS NOT NULL THEN 'Terisi' ELSE 'Tersedia' END as status
            FROM windah_basudatra.seat s
            JOIN windah_basudatra.venue v ON s.venue_id = v.venue_id
            LEFT JOIN windah_basudatra.has_relationship hr ON hr.seat_id = s.seat_id
            ORDER BY v.venue_name, s.section, s.row_number, s.seat_number
        """)
        raw_seats = _dictfetchall(cursor)

        cursor.execute("SELECT venue_id, venue_name FROM windah_basudatra.venue ORDER BY venue_name")
        venues_raw = _dictfetchall(cursor)

    seats = []
    tersedia = 0
    terisi = 0

    for s in raw_seats:
        if s['status'] == 'Tersedia':
            tersedia += 1
        else:
            terisi += 1
            
        seats.append({
            "id": str(s['seat_id']),
            "section": s['section'],
            "row": s['row'],
            "number": s['number'],
            "venue": s['venue'],
            "venue_id": str(s['venue_id']),
            "status": s['status']
        })

    venues_list = [{"id": str(v['venue_id']), "name": v['venue_name']} for v in venues_raw]
    
    context = {
        "page_title": "Manajemen Kursi",
        "seats": seats,
        "total_seats": len(seats),
        "available_seats": tersedia,
        "occupied_seats": terisi,
        "venues": venues_list,
        "show_add_button": role in ['admin', 'organizer'],
        "user_role": role,
    }
    return render(request, "manajemen_kursi.html", context)


def seat_create(request):
    role, username, redirect_response = _require_non_guest(request)
    if redirect_response: return redirect_response

    if role not in ['admin', 'organizer']:
        messages.error(request, "Hanya Admin atau Organizer yang dapat menambah kursi.")
        return redirect(f"/seats/?role={role}&username={username}")

    if request.method == "POST":
        venue_id = request.POST.get("venue_id")
        section = request.POST.get("section")
        row = request.POST.get("row")
        number = request.POST.get("number")

        seat_id = str(uuid.uuid4())

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO windah_basudatra.seat (seat_id, section, row_number, seat_number, venue_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, [seat_id, section, row, number, venue_id])
            messages.success(request, "Kursi berhasil ditambahkan.")
        except Exception as e:
            err_msg = str(e.__cause__.args[0]) if hasattr(e, "__cause__") and e.__cause__ and e.__cause__.args else str(e)
            clean_msg = err_msg.strip()
            first_line = clean_msg.splitlines()[0].strip() if clean_msg else ""
            for prefix in ('ERROR:  ', 'ERROR:', 'Error:'):
                if first_line.startswith(prefix):
                    first_line = first_line[len(prefix):].strip()
            messages.error(request, f"Gagal menambah kursi: {first_line or err_msg}")

    return redirect(f"/seats/?role={role}&username={username}")


def seat_update(request, seat_id):
    role, username, redirect_response = _require_non_guest(request)
    if redirect_response: return redirect_response

    if role not in ['admin', 'organizer']:
        messages.error(request, "Hanya Admin atau Organizer yang dapat mengubah kursi.")
        return redirect(f"/seats/?role={role}&username={username}")

    if request.method == "POST":
        venue_id = request.POST.get("venue_id")
        section = request.POST.get("section")
        row = request.POST.get("row")
        number = request.POST.get("number")

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE windah_basudatra.seat 
                    SET section = %s, row_number = %s, seat_number = %s, venue_id = %s
                    WHERE seat_id = %s
                """, [section, row, number, venue_id, seat_id])
            messages.success(request, "Kursi berhasil diupdate.")
        except Exception as e:
            err_msg = str(e.__cause__.args[0]) if hasattr(e, "__cause__") and e.__cause__ and e.__cause__.args else str(e)
            clean_msg = err_msg.strip()
            first_line = clean_msg.splitlines()[0].strip() if clean_msg else ""
            for prefix in ('ERROR:  ', 'ERROR:', 'Error:'):
                if first_line.startswith(prefix):
                    first_line = first_line[len(prefix):].strip()
            messages.error(request, f"Gagal update kursi: {first_line or err_msg}")

    return redirect(f"/seats/?role={role}&username={username}")


def seat_delete(request, seat_id):
    role, username, redirect_response = _require_non_guest(request)
    if redirect_response: return redirect_response

    if role not in ['admin', 'organizer']:
        messages.error(request, "Hanya Admin atau Organizer yang dapat menghapus kursi.")
        return redirect(f"/seats/?role={role}&username={username}")

    if request.method == "POST":
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM windah_basudatra.seat WHERE seat_id = %s", [seat_id])
            messages.success(request, "Kursi berhasil dihapus.")
        except Exception as e:
            err_msg = str(e.__cause__.args[0]) if hasattr(e, "__cause__") and e.__cause__ and e.__cause__.args else str(e)
            clean_msg = err_msg.strip()
            first_line = clean_msg.splitlines()[0].strip() if clean_msg else ""
            for prefix in ('ERROR:  ', 'ERROR:', 'Error:'):
                if first_line.startswith(prefix):
                    first_line = first_line[len(prefix):].strip()
            messages.error(request, first_line or err_msg)

    return redirect(f"/seats/?role={role}&username={username}")
