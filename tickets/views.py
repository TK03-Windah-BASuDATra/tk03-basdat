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

def manajemen_tiket(request):
    role, username, redirect_response = _require_non_guest(request)
    if redirect_response:
        return redirect_response

    try:
        # Check if status column exists in ticket table, if not, add it (safe fallback for missing spec)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema='windah_basudatra' AND table_name='ticket' AND column_name='status'
            """)
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE windah_basudatra.ticket ADD COLUMN status VARCHAR(20) DEFAULT 'Valid'")
    except Exception as e:
        pass

    with connection.cursor() as cursor:
        sql = """
            SELECT 
                t.ticket_id as id,
                t.ticket_code as code,
                e.event_title as event,
                e.event_id as event_id,
                TO_CHAR(e.event_datetime, 'YYYY-MM-DD HH24:MI') as datetime,
                v.venue_name as location,
                v.tipe_seating as seating_type,
                tc.price as price,
                tc.category_name as category_name,
                t.order_id as order_id,
                c.full_name as customer,
                COALESCE(t.status, 'Valid') as status,
                s.seat_id,
                s.section, 
                s.row_number, 
                s.seat_number
            FROM windah_basudatra.ticket t
            JOIN windah_basudatra."order" o ON t.order_id = o.order_id
            JOIN windah_basudatra.customer c ON o.customer_id = c.customer_id
            JOIN windah_basudatra.ticket_category tc ON t.category_id = tc.category_id
            JOIN windah_basudatra.event e ON tc.event_id = e.event_id
            JOIN windah_basudatra.venue v ON e.venue_id = v.venue_id
            LEFT JOIN windah_basudatra.has_relationship hr ON t.ticket_id = hr.ticket_id
            LEFT JOIN windah_basudatra.seat s ON hr.seat_id = s.seat_id
        """
        params = []
        
        if role == 'customer':
            sql += """
            JOIN windah_basudatra.user_account ua ON c.user_id = ua.user_id
            WHERE ua.username = %s
            """
            params.append(username)
            page_title = "Tiket Saya"
        else:
            page_title = "Manajemen Tiket"
            if role == 'organizer':
                # Organizer sees all tickets (as per instructions "dalam implementasi frontend ini")
                # Wait, "dalam implementasi frontend ini; di backend seharusnya di-filter per event miliknya"
                # The instructions say "Organizer melihat seluruh tiket (dalam implementasi frontend ini; di backend seharusnya di-filter per event miliknya)." 
                # Let's filter it by event miliknya anyway for completeness, or just show all if instructed.
                # Actually I'll implement the backend filter since I am writing the backend.
                sql += """
                JOIN windah_basudatra.organizer org ON e.organizer_id = org.organizer_id
                JOIN windah_basudatra.user_account ua ON org.user_id = ua.user_id
                WHERE ua.username = %s
                """
                params.append(username)
                
        sql += " ORDER BY t.ticket_code"
        cursor.execute(sql, params)
        raw_tickets = _dictfetchall(cursor)

    tickets = []
    valid_tickets = 0
    used_tickets = 0

    for rt in raw_tickets:
        if rt['status'] == 'Valid':
            valid_tickets += 1
            badge_status = 'VALID'
        elif rt['status'] == 'Used':
            used_tickets += 1
            badge_status = 'TERPAKAI'
        else:
            badge_status = rt['status'].upper()

        seat_label = f"{rt['section']} - Baris {rt['row_number']}, No. {rt['seat_number']}" if rt['seat_id'] else "-"

        tickets.append({
            "id": str(rt['id']),
            "code": rt['code'],
            "event": rt['event'],
            "event_id": str(rt['event_id']),
            "categories": [badge_status, rt['category_name'].upper()],
            "datetime": rt['datetime'],
            "location": rt['location'],
            "price": rt['price'],
            "seat": seat_label,
            "seat_id": str(rt['seat_id']) if rt['seat_id'] else "",
            "order_id": str(rt['order_id']),
            "customer": rt['customer'],
            "status": rt['status'],
        })

    # Data for Create Ticket modal
    orders = []
    categories_by_event = {}
    seats_by_event = {}

    if role in ['admin', 'organizer']:
        with connection.cursor() as cursor:
            # Get orders
            cursor.execute("""
                SELECT o.order_id, c.full_name as customer, e.event_title as event, e.event_id
                FROM windah_basudatra."order" o
                JOIN windah_basudatra.customer c ON o.customer_id = c.customer_id
                JOIN windah_basudatra.ticket t ON t.order_id = o.order_id
                JOIN windah_basudatra.ticket_category tc ON t.category_id = tc.category_id
                JOIN windah_basudatra.event e ON tc.event_id = e.event_id
                GROUP BY o.order_id, c.full_name, e.event_title, e.event_id
            """)
            for row in _dictfetchall(cursor):
                orders.append({
                    "order_id": str(row['order_id']),
                    "customer": row['customer'],
                    "event": row['event'],
                    "event_id": str(row['event_id'])
                })

            # Get categories
            cursor.execute("""
                SELECT 
                    tc.category_id, tc.event_id, tc.category_name, tc.price, tc.quota,
                    (SELECT COUNT(*) FROM windah_basudatra.ticket t WHERE t.category_id = tc.category_id) as used
                FROM windah_basudatra.ticket_category tc
            """)
            for row in _dictfetchall(cursor):
                eid = str(row['event_id'])
                if eid not in categories_by_event:
                    categories_by_event[eid] = []
                categories_by_event[eid].append({
                    "category_id": str(row['category_id']),
                    "category_name": row['category_name'],
                    "price": row['price'],
                    "used": row['used'],
                    "quota": row['quota']
                })

            # Get seats
            cursor.execute("""
                SELECT s.seat_id, s.section, s.row_number, s.seat_number, e.event_id,
                CASE WHEN hr.seat_id IS NULL THEN true ELSE false END as available
                FROM windah_basudatra.seat s
                JOIN windah_basudatra.venue v ON s.venue_id = v.venue_id
                JOIN windah_basudatra.event e ON e.venue_id = v.venue_id
                LEFT JOIN windah_basudatra.has_relationship hr ON hr.seat_id = s.seat_id
                WHERE v.tipe_seating = 'RESERVED_SEATING'
            """)
            for row in _dictfetchall(cursor):
                eid = str(row['event_id'])
                if eid not in seats_by_event:
                    seats_by_event[eid] = []
                seats_by_event[eid].append({
                    "seat_id": str(row['seat_id']),
                    "label": f"{row['section']} - Baris {row['row_number']}, No. {row['seat_number']}",
                    "available": row['available']
                })

    # Extract all seats to populate the update modal (so we can see available seats across all events)
    all_available_seats_flat = []
    for eid, slist in seats_by_event.items():
        all_available_seats_flat.extend([s for s in slist if s['available']])

    context = {
        "page_title": page_title,
        "tickets": tickets,
        "total_tickets": len(tickets),
        "valid_tickets": valid_tickets,
        "used_tickets": used_tickets,
        "show_add_button": role in ['admin', 'organizer'],
        "show_customer_column": role in ['admin', 'organizer'],
        "user_role": role,
        "can_admin_actions": role == 'admin',
        "orders": orders,
        "categories_by_event": categories_by_event,
        "seats_by_event": seats_by_event,
        "all_available_seats_flat": all_available_seats_flat,
    }
    
    return render(request, "manajemen_tiket.html", context)


def ticket_create(request):
    role, username, redirect_response = _require_non_guest(request)
    if redirect_response: return redirect_response

    if role not in ['admin', 'organizer']:
        messages.error(request, "Hanya Admin atau Organizer yang dapat membuat tiket.")
        return redirect(f"/my-tickets/?role={role}&username={username}")

    if request.method == "POST":
        order_id = request.POST.get("order_id")
        category_id = request.POST.get("category_id")
        seat_id = request.POST.get("seat_id")

        if not order_id or not category_id:
            messages.error(request, "Order dan Kategori Tiket wajib diisi.")
            return redirect(f"/my-tickets/?role={role}&username={username}")

        ticket_id = str(uuid.uuid4())
        ticket_code = f"TIK-{uuid.uuid4().hex[:8].upper()}"

        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO windah_basudatra.ticket (ticket_id, ticket_code, category_id, order_id)
                        VALUES (%s, %s, %s, %s)
                    """, [ticket_id, ticket_code, category_id, order_id])

                    # Assign seat if provided
                    if seat_id:
                        cursor.execute("""
                            INSERT INTO windah_basudatra.has_relationship (seat_id, ticket_id)
                            VALUES (%s, %s)
                        """, [seat_id, ticket_id])
                        
            messages.success(request, f"Tiket baru berhasil dibuat dengan kode {ticket_code}")
        except Exception as e:
            err_msg = str(e.__cause__.args[0]) if hasattr(e, "__cause__") and e.__cause__ and e.__cause__.args else str(e)
            clean_msg = err_msg.strip()
            first_line = clean_msg.splitlines()[0].strip() if clean_msg else ""
            for prefix in ('ERROR:  ', 'ERROR:', 'Error:'):
                if first_line.startswith(prefix):
                    first_line = first_line[len(prefix):].strip()
            
            messages.error(request, first_line or err_msg)

    return redirect(f"/my-tickets/?role={role}&username={username}")


def ticket_update(request, ticket_id):
    role, username, redirect_response = _require_non_guest(request)
    if redirect_response: return redirect_response

    if role != 'admin':
        messages.error(request, "Hanya Admin yang dapat mengubah tiket.")
        return redirect(f"/my-tickets/?role={role}&username={username}")

    if request.method == "POST":
        status = request.POST.get("status")
        seat_id = request.POST.get("seat_id")

        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Update status
                    cursor.execute("""
                        UPDATE windah_basudatra.ticket 
                        SET status = %s 
                        WHERE ticket_id = %s
                    """, [status, ticket_id])

                    # Manage seat assignment
                    cursor.execute("DELETE FROM windah_basudatra.has_relationship WHERE ticket_id = %s", [ticket_id])
                    if seat_id:
                        cursor.execute("""
                            INSERT INTO windah_basudatra.has_relationship (seat_id, ticket_id)
                            VALUES (%s, %s)
                        """, [seat_id, ticket_id])

            messages.success(request, "Tiket berhasil diupdate.")
        except Exception as e:
            err_msg = str(e.__cause__.args[0]) if hasattr(e, "__cause__") and e.__cause__ and e.__cause__.args else str(e)
            clean_msg = err_msg.strip()
            first_line = clean_msg.splitlines()[0].strip() if clean_msg else ""
            for prefix in ('ERROR:  ', 'ERROR:', 'Error:'):
                if first_line.startswith(prefix):
                    first_line = first_line[len(prefix):].strip()
            messages.error(request, first_line or err_msg)

    return redirect(f"/my-tickets/?role={role}&username={username}")


def ticket_delete(request, ticket_id):
    role, username, redirect_response = _require_non_guest(request)
    if redirect_response: return redirect_response

    if role != 'admin':
        messages.error(request, "Hanya Admin yang dapat menghapus tiket.")
        return redirect(f"/my-tickets/?role={role}&username={username}")

    if request.method == "POST":
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM windah_basudatra.has_relationship WHERE ticket_id = %s", [ticket_id])
                    cursor.execute("DELETE FROM windah_basudatra.ticket WHERE ticket_id = %s", [ticket_id])
                    
            messages.success(request, "Tiket berhasil dihapus.")
        except Exception as e:
            err_msg = str(e.__cause__.args[0]) if hasattr(e, "__cause__") and e.__cause__ and e.__cause__.args else str(e)
            clean_msg = err_msg.strip()
            first_line = clean_msg.splitlines()[0].strip() if clean_msg else ""
            for prefix in ('ERROR:  ', 'ERROR:', 'Error:'):
                if first_line.startswith(prefix):
                    first_line = first_line[len(prefix):].strip()
            messages.error(request, first_line or err_msg)

    return redirect(f"/my-tickets/?role={role}&username={username}")
