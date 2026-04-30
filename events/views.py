from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace

from django import forms
from django.contrib import messages
from django.db import connection
from django.forms import formset_factory
from django.shortcuts import redirect, render
from django.urls import reverse

VALID_ROLES = ["guest", "admin", "organizer", "customer"]

def _safe_role(role, default="guest"):
    return role if role in VALID_ROLES else default


def _current_role(request):
    return _safe_role(request.GET.get("role", "guest"))

def _with_role(url_name, role, *args):
    return f"{reverse(url_name, args=args)}?role={role}"

def can_manage(role):
    return role in ["admin", "organizer"]

def _dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

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
    with connection.cursor() as cursor:
        cursor.execute("""
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
        """)
        rows = _dictfetchall(cursor)

    venues = []
    for row in rows:
        seating_type = "reserved" if int(row["seat_count"] or 0) > 0 else "free"
        venues.append(
            VenueView(
                venue_id=str(row["venue_id"]),
                venue_name=row["venue_name"],
                capacity=row["capacity"],
                address=row["address"],
                city=row["city"],
                seating_type=seating_type,
            )
        )
    return venues

def _load_ticket_categories_by_event():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                event_id,
                category_name,
                price,
                quota
            FROM ticket_category
            ORDER BY category_name
        """)
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

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                e.event_id,
                e.event_title,
                e.event_datetime,
                e.venue_id,
                o.organizer_name,
                COALESCE(STRING_AGG(DISTINCT a.name, ', '), '-') AS artists
            FROM event e
            JOIN organizer o ON o.organizer_id = e.organizer_id
            LEFT JOIN event_artist ea ON ea.event_id = e.event_id
            LEFT JOIN artist a ON a.artist_id = ea.artist_id
            GROUP BY
                e.event_id,
                e.event_title,
                e.event_datetime,
                e.venue_id,
                o.organizer_name
            ORDER BY e.event_datetime
        """)
        rows = _dictfetchall(cursor)

    events = []
    for row in rows:
        event_id = str(row["event_id"])
        venue = venue_map.get(str(row["venue_id"]))
        tickets = ticket_map.get(event_id, [])

        events.append(
            EventView(
                event_id=event_id,
                event_title=row["event_title"],
                event_datetime=row["event_datetime"],
                venue=venue,
                organizer=SimpleNamespace(username=row["organizer_name"]),
                artists=row["artists"] or "-",
                description=f"Event {row['event_title']} di {venue.venue_name if venue else 'venue pilihan'}.",
                image_url="",
                ticket_categories=TicketCategoryCollection(tickets),
            )
        )

    return events

def _find_venue(pk):
    pk = str(pk)
    for venue in _load_venues():
        if venue.venue_id == pk:
            return venue
    return None


def _find_event(pk):
    pk = str(pk)
    for event in _load_events():
        if event.event_id == pk:
            return event
    return None

class VenueDummyForm(forms.Form):
    venue_name = forms.CharField(label="Nama Venue", max_length=100)
    capacity = forms.IntegerField(label="Kapasitas", min_value=1)
    city = forms.CharField(label="Kota", max_length=100)
    address = forms.CharField(label="Alamat", widget=forms.Textarea(attrs={"rows": 3}))
    seating_type = forms.ChoiceField(
        label="Tipe Seating",
        choices=[
            ("reserved", "Reserved"),
            ("free", "Free"),
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "address":
                field.widget.attrs.update({"class": "form-control"})
            elif name == "seating_type":
                field.widget.attrs.update({"class": "form-select"})
            else:
                field.widget.attrs.update({"class": "form-control"})

class EventDummyForm(forms.Form):
    event_title = forms.CharField(label="Judul Event", max_length=150)
    venue = forms.ChoiceField(label="Venue")
    event_datetime = forms.DateTimeField(
        label="Tanggal & Waktu Event",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
    )
    image_url = forms.URLField(label="Image URL", required=False)
    artists = forms.CharField(label="Artis", max_length=255)
    description = forms.CharField(label="Deskripsi", widget=forms.Textarea(attrs={"rows": 4}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["venue"].choices = [
            (v.venue_id, v.venue_name) for v in _load_venues()
        ]

        for name, field in self.fields.items():
            if name == "venue":
                field.widget.attrs.update({"class": "form-select"})
            elif name == "description":
                field.widget.attrs.update({"class": "form-control"})
            elif name != "event_datetime":
                field.widget.attrs.update({"class": "form-control"})

class TicketCategoryDummyForm(forms.Form):
    category_name = forms.CharField(label="Nama Kategori", max_length=100)
    price = forms.IntegerField(label="Harga", min_value=0)
    quota = forms.IntegerField(label="Kuota", min_value=1)
    DELETE = forms.BooleanField(label="Hapus", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "DELETE":
                continue
            field.widget.attrs.update({"class": "form-control"})

TicketCategoryFormSet = formset_factory(
    TicketCategoryDummyForm,
    extra=1,
    can_delete=True,
)

def venue_list(request):
    role = _current_role(request)
    all_venues = _load_venues()
    venues = list(all_venues)

    q = request.GET.get("q", "").strip().lower()
    city = request.GET.get("city", "").strip()
    seating = request.GET.get("seating", "").strip()

    if q:
        venues = [
            v for v in venues
            if q in v.venue_name.lower() or q in v.address.lower()
        ]

    if city:
        venues = [v for v in venues if v.city.lower() == city.lower()]

    if seating:
        venues = [v for v in venues if v.seating_type == seating]

    stats = {
        "total_venue": len(all_venues),
        "reserved_count": sum(1 for v in all_venues if v.seating_type == "reserved"),
        "total_capacity": sum(v.capacity for v in all_venues),
    }

    context = {
        "venues": venues,
        "stats": stats,
        "can_manage": can_manage(role),
        "cities": sorted({v.city for v in all_venues}),
    }
    return render(request, "venue_list.html", context)

def venue_create(request):
    role = _current_role(request)

    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa menambah venue.")
        return redirect(_with_role("events:venue_list", role))

    if request.method == "POST":
        form = VenueDummyForm(request.POST)
        if form.is_valid():
            messages.success(request, "Simulasi tambah venue berhasil.")
            return redirect(_with_role("events:venue_list", role))
    else:
        form = VenueDummyForm()

    return render(request, "venue_form.html", {
        "form": form,
        "title": "Tambah Venue",
    })

def venue_update(request, pk):
    role = _current_role(request)

    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa mengubah venue.")
        return redirect(_with_role("events:venue_list", role))

    venue = _find_venue(pk)
    if not venue:
        messages.error(request, "Venue tidak ditemukan.")
        return redirect(_with_role("events:venue_list", role))

    initial = {
        "venue_name": venue.venue_name,
        "capacity": venue.capacity,
        "city": venue.city,
        "address": venue.address,
        "seating_type": venue.seating_type,
    }

    if request.method == "POST":
        form = VenueDummyForm(request.POST)
        if form.is_valid():
            messages.success(request, "Simulasi edit venue berhasil.")
            return redirect(_with_role("events:venue_list", role))
    else:
        form = VenueDummyForm(initial=initial)

    return render(request, "venue_form.html", {
        "form": form,
        "title": "Edit Venue",
    })

def venue_delete(request, pk):
    role = _current_role(request)

    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa menghapus venue.")
        return redirect(_with_role("events:venue_list", role))

    venue = _find_venue(pk)
    if not venue:
        messages.error(request, "Venue tidak ditemukan.")
        return redirect(_with_role("events:venue_list", role))

    if request.method == "POST":
        messages.success(request, "Simulasi hapus venue berhasil.")
        return redirect(_with_role("events:venue_list", role))

    return render(request, "venue_confirm_delete.html", {
        "venue": venue,
    })

def event_list(request):
    role = _current_role(request)
    events = _load_events()

    q = request.GET.get("q", "").strip().lower()
    venue_id = request.GET.get("venue", "").strip()
    artist = request.GET.get("artist", "").strip().lower()

    if q:
        events = [
            e for e in events
            if q in e.event_title.lower() or q in e.artists.lower()
        ]

    if venue_id:
        events = [e for e in events if e.venue and e.venue.venue_id == venue_id]

    if artist:
        events = [e for e in events if artist in e.artists.lower()]

    context = {
        "events": events,
        "venues": _load_venues(),
        "role": role,
    }
    return render(request, "event_list.html", context)

def event_manage_list(request):
    role = _current_role(request)

    if not can_manage(role):
        messages.error(request, "Halaman ini hanya untuk admin atau organizer.")
        return redirect(_with_role("dashboard", role))

    events = _load_events()

    context = {
        "events": events,
    }
    return render(request, "event_manage_list.html", context)

def event_create(request):
    role = _current_role(request)

    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa membuat event.")
        return redirect(_with_role("dashboard", role))

    if request.method == "POST":
        form = EventDummyForm(request.POST)
        formset = TicketCategoryFormSet(request.POST, prefix="ticket_categories")

        if form.is_valid() and formset.is_valid():
            messages.success(request, "Simulasi buat event berhasil.")
            return redirect(_with_role("events:event_manage_list", role))
    else:
        form = EventDummyForm()
        formset = TicketCategoryFormSet(prefix="ticket_categories")

    return render(request, "event_form.html", {
        "form": form,
        "formset": formset,
        "title": "Buat Event",
    })

def event_update(request, pk):
    role = _current_role(request)

    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa mengubah event.")
        return redirect(_with_role("dashboard", role))

    event = _find_event(pk)
    if not event:
        messages.error(request, "Event tidak ditemukan.")
        return redirect(_with_role("events:event_manage_list", role))

    initial_form = {
        "event_title": event.event_title,
        "venue": event.venue.venue_id if event.venue else "",
        "event_datetime": event.event_datetime.strftime("%Y-%m-%dT%H:%M"),
        "image_url": event.image_url,
        "artists": event.artists,
        "description": event.description,
    }

    initial_formset = [
        {
            "category_name": ticket.category_name,
            "price": int(ticket.price),
            "quota": ticket.quota,
        }
        for ticket in event.ticket_categories.all()
    ]

    if request.method == "POST":
        form = EventDummyForm(request.POST)
        formset = TicketCategoryFormSet(request.POST, prefix="ticket_categories")

        if form.is_valid() and formset.is_valid():
            messages.success(request, "Simulasi edit event berhasil.")
            return redirect(_with_role("events:event_manage_list", role))
    else:
        form = EventDummyForm(initial=initial_form)
        formset = TicketCategoryFormSet(initial=initial_formset, prefix="ticket_categories")

    return render(request, "event_form.html", {
        "form": form,
        "formset": formset,
        "title": "Edit Event",
    })

def event_delete(request, pk):
    role = _current_role(request)

    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa menghapus event.")
        return redirect(_with_role("events:event_manage_list", role))

    event = _find_event(pk)
    if not event:
        messages.error(request, "Event tidak ditemukan.")
        return redirect(_with_role("events:event_manage_list", role))

    if request.method == "POST":
        messages.success(request, "Event berhasil dihapus.")
        return redirect(_with_role("events:event_manage_list", role))

    return render(request, "event_confirm_delete.html", {
        "event": event,
    })