from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from types import SimpleNamespace
from django.contrib import messages
from django.db import DatabaseError, connection, transaction
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse
from .forms import EventForm, TicketCategoryFormSet, VenueForm, EventArtistFormSet

VALID_ROLES = ["guest", "admin", "organizer", "customer"]

def _safe_role(role, default="guest"):
    return role if role in VALID_ROLES else default

def _current_role(request):
    return _safe_role(request.GET.get("role") or request.POST.get("role") or "guest")

def can_manage(role):
    return role in ["admin", "organizer"]

def _with_role(url_name, role, *args):
    return f"{reverse(url_name, args=args)}?role={role}"

def _dashboard_or_event_list(role):
    try:
        return _with_role("dashboard", role)
    except NoReverseMatch:
        return _with_role("events:event_list", role)

def _dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def _db_error_message(exc):
    cause = getattr(exc, "__cause__", None)
    diag = getattr(cause, "diag", None)
    primary = getattr(diag, "message_primary", None)
    if primary:
        return primary
    return str(exc).split("\n")[0]

@lru_cache(maxsize=None)
def _table_columns(table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
            AND table_name = %s
            """,
            [table_name],
        )
        return {row[0] for row in cursor.fetchall()}

def _table_exists(table_name):
    return bool(_table_columns(table_name))

@dataclass
class VenueView:
    venue_id: str
    venue_name: str
    capacity: int
    address: str
    city: str
    seating_type: str

    def get_seating_type_display(self):
        return "Reserved" if self.seating_type == "reserved" else "Free"

@dataclass
class TicketCategoryView:
    category_name: str
    price: float
    quota: int

class TicketCategoryCollection:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items

@dataclass
class EventView:
    event_id: str
    event_title: str
    event_datetime: datetime
    venue: VenueView
    organizer: object
    artists: str
    description: str
    image_url: str
    ticket_categories: TicketCategoryCollection

    @property
    def min_ticket_price(self):
        prices = [ticket.price for ticket in self.ticket_categories.all()]
        return min(prices) if prices else 0

def _load_venues():
    has_seat_table = _table_exists("seat") and "venue_id" in _table_columns("seat")

    if has_seat_table:
        sql = """
            SELECT
                v.venue_id,
                v.venue_name,
                v.capacity,
                v.address,
                v.city,
                COUNT(s.seat_id) AS seat_count
            FROM venue v
            LEFT JOIN seat s ON s.venue_id = v.venue_id
            GROUP BY v.venue_id, v.venue_name, v.capacity, v.address, v.city
            ORDER BY v.venue_name
        """
    else:
        sql = """
            SELECT
                v.venue_id,
                v.venue_name,
                v.capacity,
                v.address,
                v.city,
                0 AS seat_count
            FROM venue v
            ORDER BY v.venue_name
        """

    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = _dictfetchall(cursor)

    return [
        VenueView(
            venue_id=str(row["venue_id"]),
            venue_name=row["venue_name"],
            capacity=row["capacity"],
            address=row["address"],
            city=row["city"],
            seating_type="reserved" if int(row["seat_count"] or 0) > 0 else "free",
        )
        for row in rows
    ]

def _find_venue(pk):
    pk = str(pk)
    for venue in _load_venues():
        if venue.venue_id == pk:
            return venue
    return None

def _load_ticket_categories_by_event():
    if not _table_exists("ticket_category"):
        return defaultdict(list)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT event_id, category_name, price, quota
            FROM ticket_category
            ORDER BY category_name
            """
        )
        rows = _dictfetchall(cursor)

    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row["event_id"])].append(
            TicketCategoryView(
                category_name=row["category_name"],
                price=float(row["price"]),
                quota=row["quota"],
            )
        )
    return grouped

def _load_events():
    venues = _load_venues()
    venue_map = {v.venue_id: v for v in venues}
    ticket_map = _load_ticket_categories_by_event()

    event_cols = _table_columns("event")
    description_sql = "e.description" if "description" in event_cols else "NULL::text"
    image_sql = "e.image_url" if "image_url" in event_cols else "NULL::text"

    has_artist_join = _table_exists("event_artist") and _table_exists("artist")
    artist_sql = "COALESCE(STRING_AGG(DISTINCT a.name, ', '), '-')" if has_artist_join else "'-'"
    artist_join_sql = """
            LEFT JOIN event_artist ea ON ea.event_id = e.event_id
            LEFT JOIN artist a ON a.artist_id = ea.artist_id
    """ if has_artist_join else ""

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                e.event_id,
                e.event_title,
                e.event_datetime,
                e.venue_id,
                o.organizer_name,
                {description_sql} AS description,
                {image_sql} AS image_url,
                {artist_sql} AS artists
            FROM event e
            JOIN organizer o ON o.organizer_id = e.organizer_id
            {artist_join_sql}
            GROUP BY
                e.event_id,
                e.event_title,
                e.event_datetime,
                e.venue_id,
                o.organizer_name
            ORDER BY e.event_datetime
            """
        )
        rows = _dictfetchall(cursor)

    events = []
    for row in rows:
        event_id = str(row["event_id"])
        venue = venue_map.get(str(row["venue_id"]))
        description = row.get("description") or (
            f"Event {row['event_title']} di {venue.venue_name if venue else 'venue pilihan'}."
        )

        events.append(
            EventView(
                event_id=event_id,
                event_title=row["event_title"],
                event_datetime=row["event_datetime"],
                venue=venue,
                organizer=SimpleNamespace(username=row["organizer_name"]),
                artists=row.get("artists") or "-",
                description=description,
                image_url=row.get("image_url") or "",
                ticket_categories=TicketCategoryCollection(ticket_map.get(event_id, [])),
            )
        )
    return events

def _find_event(pk):
    pk = str(pk)
    for event in _load_events():
        if event.event_id == pk:
            return event
    return None

def _post_object_id(request, key):
    return request.POST.get(key, "").strip()

def _sync_seats(cursor, venue_id, capacity, seating_type):
    seat_cols = _table_columns("seat")
    if "venue_id" not in seat_cols:
        return

    cursor.execute("DELETE FROM seat WHERE venue_id = %s", [venue_id])

    if seating_type != "reserved":
        return

    if {"section", "seat_number", "row_number"}.issubset(seat_cols):
        cursor.execute(
            """
            INSERT INTO seat (seat_id, section, seat_number, row_number, venue_id)
            SELECT
                gen_random_uuid(),
                'Regular',
                CONCAT('S', LPAD((((gs - 1) %% 50) + 1)::text, 3, '0')),
                CONCAT('R', CEIL(gs / 50.0)::int),
                %s
            FROM generate_series(1, %s) AS gs
            """,
            [venue_id, capacity],
        )
    elif "seat_number" in seat_cols:
        cursor.execute(
            """
            INSERT INTO seat (seat_id, venue_id, seat_number)
            SELECT gen_random_uuid(), %s, CONCAT('S', gs)
            FROM generate_series(1, %s) AS gs
            """,
            [venue_id, capacity],
        )
    elif "seat_label" in seat_cols:
        cursor.execute(
            """
            INSERT INTO seat (seat_id, venue_id, seat_label)
            SELECT gen_random_uuid(), %s, CONCAT('S', gs)
            FROM generate_series(1, %s) AS gs
            """,
            [venue_id, capacity],
        )
    else:
        cursor.execute(
            """
            INSERT INTO seat (seat_id, venue_id)
            SELECT gen_random_uuid(), %s
            FROM generate_series(1, %s)
            """,
            [venue_id, capacity],
        )

def _current_organizer_id(request):
    organizer_id = request.POST.get("organizer_id") or request.GET.get("organizer_id")
    if organizer_id:
        return organizer_id

    with connection.cursor() as cursor:
        cursor.execute("SELECT organizer_id FROM organizer ORDER BY organizer_name LIMIT 1")
        row = cursor.fetchone()

    if not row:
        raise DatabaseError("Tidak ada data organizer. Tambahkan dummy data organizer terlebih dahulu.")
    return row[0]

def _clean_ticket_forms(formset):
    tickets = []
    for form in formset:
        if not form.cleaned_data or form.cleaned_data.get("DELETE"):
            continue
        tickets.append(
            {
                "category_name": form.cleaned_data["category_name"],
                "price": form.cleaned_data["price"],
                "quota": form.cleaned_data["quota"],
            }
        )
    return tickets

def _sync_ticket_categories(cursor, event_id, tickets):
    if not _table_exists("ticket_category"):
        return

    cursor.execute("DELETE FROM ticket_category WHERE event_id = %s", [event_id])
    for ticket in tickets:
        cursor.execute(
            """
            INSERT INTO ticket_category (event_id, category_name, price, quota)
            VALUES (%s, %s, %s, %s)
            """,
            [event_id, ticket["category_name"], ticket["price"], ticket["quota"]],
        )

def venue_list(request):
    role = _current_role(request)
    all_venues = _load_venues()
    venues = list(all_venues)

    q = request.GET.get("q", "").strip().lower()
    city = request.GET.get("city", "").strip()
    seating = request.GET.get("seating", "").strip()

    if q:
        venues = [v for v in venues if q in v.venue_name.lower() or q in v.address.lower()]
    if city:
        venues = [v for v in venues if v.city.lower() == city.lower()]
    if seating:
        venues = [v for v in venues if v.seating_type == seating]

    return render(
        request,
        "venue_list.html",
        {
            "venues": venues,
            "role": role,
            "can_manage": can_manage(role),
            "cities": sorted({v.city for v in all_venues}),
            "stats": {
                "total_venue": len(all_venues),
                "reserved_count": sum(1 for v in all_venues if v.seating_type == "reserved"),
                "total_capacity": sum(v.capacity for v in all_venues),
            },
        },
    )

def venue_create(request):
    role = _current_role(request)
    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa menambah venue.")
        return redirect(_with_role("events:venue_list", role))

    if request.method == "POST":
        form = VenueForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT sp_create_venue(%s, %s, %s, %s)",
                        [
                            form.cleaned_data["venue_name"],
                            form.cleaned_data["capacity"],
                            form.cleaned_data["address"],
                            form.cleaned_data["city"],
                        ],
                    )
                    venue_id = cursor.fetchone()[0]
                    _sync_seats(
                        cursor,
                        venue_id,
                        form.cleaned_data["capacity"],
                        form.cleaned_data["seating_type"],
                    )
                messages.success(request, "Venue berhasil ditambahkan.")
                return redirect(_with_role("events:venue_list", role))
            except DatabaseError as exc:
                messages.error(request, _db_error_message(exc))
    else:
        form = VenueForm()

    return render(request, "venue_form.html", {"form": form, "title": "Tambah Venue", "role": role})

def venue_update(request):
    role = _current_role(request)
    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa mengubah venue.")
        return redirect(_with_role("events:venue_list", role))

    if request.method != "POST":
        return redirect(_with_role("events:venue_list", role))

    venue_id = _post_object_id(request, "venue_id")
    venue = _find_venue(venue_id)
    if not venue:
        messages.error(request, "Venue tidak ditemukan.")
        return redirect(_with_role("events:venue_list", role))

    mode = request.POST.get("mode", "open")
    initial = {
        "venue_name": venue.venue_name,
        "capacity": venue.capacity,
        "city": venue.city,
        "address": venue.address,
        "seating_type": venue.seating_type,
    }

    if mode == "save":
        form = VenueForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT sp_update_venue(%s, %s, %s, %s, %s)",
                        [
                            venue_id,
                            form.cleaned_data["venue_name"],
                            form.cleaned_data["capacity"],
                            form.cleaned_data["address"],
                            form.cleaned_data["city"],
                        ],
                    )
                    if (
                        form.cleaned_data["capacity"] != venue.capacity
                        or form.cleaned_data["seating_type"] != venue.seating_type
                    ):
                        _sync_seats(
                            cursor,
                            venue_id,
                            form.cleaned_data["capacity"],
                            form.cleaned_data["seating_type"],
                        )
                messages.success(request, "Venue berhasil diperbarui.")
                return redirect(_with_role("events:venue_list", role))
            except DatabaseError as exc:
                messages.error(request, _db_error_message(exc))
    else:
        form = VenueForm(initial=initial)

    return render(
        request,
        "venue_form.html",
        {"form": form, "title": "Edit Venue", "venue_id": venue_id, "mode": "save", "role": role},
    )

def venue_delete(request):
    role = _current_role(request)
    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa menghapus venue.")
        return redirect(_with_role("events:venue_list", role))

    if request.method != "POST":
        return redirect(_with_role("events:venue_list", role))

    venue_id = _post_object_id(request, "venue_id")
    venue = _find_venue(venue_id)
    if not venue:
        messages.error(request, "Venue tidak ditemukan.")
        return redirect(_with_role("events:venue_list", role))

    if request.POST.get("mode") == "confirm":
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                if _table_exists("seat") and "venue_id" in _table_columns("seat"):
                    cursor.execute("DELETE FROM seat WHERE venue_id = %s", [venue_id])
                cursor.execute("SELECT sp_delete_venue(%s)", [venue_id])
            messages.success(request, "Venue berhasil dihapus.")
            return redirect(_with_role("events:venue_list", role))
        except DatabaseError as exc:
            messages.error(request, _db_error_message(exc))
            return redirect(_with_role("events:venue_list", role))

    return render(request, "venue_confirm_delete.html", {"venue": venue, "venue_id": venue_id, "role": role})

def event_list(request):
    role = _current_role(request)
    events = _load_events()

    q = request.GET.get("q", "").strip().lower()
    venue_id = request.GET.get("venue", "").strip()
    artist = request.GET.get("artist", "").strip().lower()

    if q:
        events = [e for e in events if q in e.event_title.lower() or q in e.artists.lower()]
    if venue_id:
        events = [e for e in events if e.venue and e.venue.venue_id == venue_id]
    if artist:
        events = [e for e in events if artist in e.artists.lower()]

    return render(request, "event_list.html", {"events": events, "venues": _load_venues(), "role": role})

def event_manage_list(request):
    role = _current_role(request)
    if not can_manage(role):
        messages.error(request, "Halaman ini hanya untuk admin atau organizer.")
        return redirect(_dashboard_or_event_list(role))

    return render(request, "event_manage_list.html", {"events": _load_events(), "role": role})

def event_create(request):
    role = _current_role(request)
    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa membuat event.")
        return redirect(_dashboard_or_event_list(role))

    venues = _load_venues()
    artist_choices = _load_artist_choices()
    if request.method == "POST":
        form = EventForm(request.POST, venues=venues)
        formset = TicketCategoryFormSet(request.POST, prefix="ticket_categories")
        artist_formset = EventArtistFormSet(
            request.POST or None,
            prefix="event_artists",
            form_kwargs={"artist_choices": artist_choices},
        )
        if form.is_valid() and formset.is_valid() and artist_formset.is_valid():
            try:
                tickets = _clean_ticket_forms(formset)
                with transaction.atomic(), connection.cursor() as cursor:
                    event_cols = _table_columns("event")
                    insert_cols = ["event_id", "event_title", "event_datetime", "venue_id", "organizer_id"]
                    values_sql = ["gen_random_uuid()", "%s", "%s", "%s", "%s"]
                    params = [
                        form.cleaned_data["event_title"],
                        form.cleaned_data["event_datetime"],
                        form.cleaned_data["venue"],
                        _current_organizer_id(request),
                    ]

                    if "description" in event_cols:
                        insert_cols.append("description")
                        values_sql.append("%s")
                        params.append(form.cleaned_data.get("description") or "")
                    if "image_url" in event_cols:
                        insert_cols.append("image_url")
                        values_sql.append("%s")
                        params.append(form.cleaned_data.get("image_url") or "")

                    cursor.execute(
                        f"""
                        INSERT INTO event ({', '.join(insert_cols)})
                        VALUES ({', '.join(values_sql)})
                        RETURNING event_id
                        """,
                        params,
                    )
                    event_id = cursor.fetchone()[0]
                    _save_event_artists(cursor, event_id, artist_formset)
                    _sync_ticket_categories(cursor, event_id, tickets)

                messages.success(request, "Event berhasil dibuat.")
                return redirect(_with_role("events:event_manage_list", role))
            except DatabaseError as exc:
                messages.error(request, _db_error_message(exc))
    else:
        form = EventForm(venues=venues)
        formset = TicketCategoryFormSet(prefix="ticket_categories")
        artist_formset = EventArtistFormSet(
            prefix="event_artists",
            form_kwargs={"artist_choices": artist_choices},
        )

    return render(request, "event_form.html", {"form": form, "formset": formset, "title": "Buat Event", "role": role, "artist_formset": artist_formset, })

def event_update(request):
    role = _current_role(request)
    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa mengubah event.")
        return redirect(_dashboard_or_event_list(role))

    if request.method != "POST":
        return redirect(_with_role("events:event_manage_list", role))

    event_id = _post_object_id(request, "event_id")
    event = _find_event(event_id)
    if not event:
        messages.error(request, "Event tidak ditemukan.")
        return redirect(_with_role("events:event_manage_list", role))

    venues = _load_venues()
    artist_choices = _load_artist_choices()
    mode = request.POST.get("mode", "open")

    if mode == "save":
        form = EventForm(request.POST, venues=venues)
        formset = TicketCategoryFormSet(request.POST, prefix="ticket_categories")
        artist_formset = EventArtistFormSet(
            request.POST,
            prefix="event_artists",
            form_kwargs={"artist_choices": artist_choices},
        )

        if form.is_valid() and formset.is_valid() and artist_formset.is_valid():
            try:
                tickets = _clean_ticket_forms(formset)
                with transaction.atomic(), connection.cursor() as cursor:
                    event_cols = _table_columns("event")
                    set_sql = ["event_title = %s", "event_datetime = %s", "venue_id = %s"]
                    params = [
                        form.cleaned_data["event_title"],
                        form.cleaned_data["event_datetime"],
                        form.cleaned_data["venue"],
                    ]

                    if "description" in event_cols:
                        set_sql.append("description = %s")
                        params.append(form.cleaned_data.get("description") or "")
                    if "image_url" in event_cols:
                        set_sql.append("image_url = %s")
                        params.append(form.cleaned_data.get("image_url") or "")

                    params.append(event_id)
                    cursor.execute(
                        f"UPDATE event SET {', '.join(set_sql)} WHERE event_id = %s",
                        params,
                    )
                    _save_event_artists(cursor, event_id, artist_formset)
                    _sync_ticket_categories(cursor, event_id, tickets)

                messages.success(request, "Event berhasil diperbarui.")
                return redirect(_with_role("events:event_manage_list", role))
            except DatabaseError as exc:
                messages.error(request, _db_error_message(exc))
    else:
        form = EventForm(
            initial={
                "event_title": event.event_title,
                "venue": event.venue.venue_id if event.venue else "",
                "event_datetime": event.event_datetime.strftime("%Y-%m-%dT%H:%M"),
                "image_url": event.image_url,
                "description": event.description,
            },
            venues=venues,
        )
        formset = TicketCategoryFormSet(
            initial=[
                {"category_name": t.category_name, "price": int(t.price), "quota": t.quota}
                for t in event.ticket_categories.all()
            ],
            prefix="ticket_categories",
        )
        artist_formset = EventArtistFormSet(
            initial=_load_event_artist_initial(event_id),
            prefix="event_artists",
            form_kwargs={"artist_choices": artist_choices},
        )

    return render(
        request,
        "event_form.html",
        {
            "form": form,
            "formset": formset,
            "artist_formset": artist_formset,
            "title": "Edit Event",
            "event_id": event_id,
            "mode": "save",
            "role": role,
        },
    )

def event_delete(request):
    role = _current_role(request)
    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa menghapus event.")
        return redirect(_with_role("events:event_manage_list", role))

    if request.method != "POST":
        return redirect(_with_role("events:event_manage_list", role))

    event_id = _post_object_id(request, "event_id")
    event = _find_event(event_id)
    if not event:
        messages.error(request, "Event tidak ditemukan.")
        return redirect(_with_role("events:event_manage_list", role))

    if request.POST.get("mode") == "confirm":
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                if _table_exists("ticket_category"):
                    cursor.execute("DELETE FROM ticket_category WHERE event_id = %s", [event_id])
                if _table_exists("event_artist"):
                    cursor.execute("DELETE FROM event_artist WHERE event_id = %s", [event_id])
                cursor.execute("DELETE FROM event WHERE event_id = %s", [event_id])
            messages.success(request, "Event berhasil dihapus.")
            return redirect(_with_role("events:event_manage_list", role))
        except DatabaseError as exc:
            messages.error(request, _db_error_message(exc))
            return redirect(_with_role("events:event_manage_list", role))

    return render(request, "event_confirm_delete.html", {"event": event, "event_id": event_id, "role": role})

def _load_artist_choices():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT artist_id, name
            FROM artist
            ORDER BY name
        """)
        rows = cursor.fetchall()

    return [("", "Pilih artis")] + [(str(row[0]), row[1]) for row in rows]

def _load_event_artist_initial(event_id):
    if not (_table_exists("event_artist") and _table_exists("artist")):
        return []

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT ea.artist_id, ea.role
            FROM event_artist ea
            JOIN artist a ON a.artist_id = ea.artist_id
            WHERE ea.event_id = %s
            ORDER BY a.name
            """,
            [event_id],
        )
        rows = cursor.fetchall()

    return [
        {
            "artist": str(row[0]),
            "role": row[1] or "",
        }
        for row in rows
    ]

def _save_event_artists(cursor, event_id, artist_formset):
    if not _table_exists("event_artist"):
        return

    cursor.execute("DELETE FROM event_artist WHERE event_id = %s", [event_id])

    for artist_form in artist_formset:
        if not artist_form.cleaned_data:
            continue

        if artist_form.cleaned_data.get("DELETE"):
            continue

        artist_id = artist_form.cleaned_data.get("artist")
        artist_role = artist_form.cleaned_data.get("role")

        if not artist_id or not artist_role:
            continue

        cursor.execute(
            """
            INSERT INTO event_artist (event_id, artist_id, role)
            VALUES (%s, %s, %s)
            """,
            [event_id, artist_id, artist_role],
        )
