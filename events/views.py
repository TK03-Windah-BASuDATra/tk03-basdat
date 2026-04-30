from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EventForm, TicketCategoryFormSet, VenueForm
from .models import Event, Venue

VALID_ROLES = ["guest", "admin", "organizer", "customer"]


def _safe_role(role, default="guest"):
    return role if role in VALID_ROLES else default


def _current_role(request):
    return _safe_role(request.GET.get("role", "guest"))


def _with_role(url_name, role, *args):
    from django.urls import reverse
    return f"{reverse(url_name, args=args)}?role={role}"


def can_manage(role):
    return role in ["admin", "organizer"]


def is_admin(role):
    return role == "admin"


def venue_list(request):
    role = _current_role(request)
    venues = Venue.objects.all()

    q = request.GET.get("q", "")
    city = request.GET.get("city", "")
    seating = request.GET.get("seating", "")

    if q:
        venues = venues.filter(
            Q(venue_name__icontains=q) |
            Q(address__icontains=q)
        )

    if city:
        venues = venues.filter(city__iexact=city)

    if seating:
        venues = venues.filter(seating_type=seating)

    stats = {
        "total_venue": Venue.objects.count(),
        "reserved_count": Venue.objects.filter(seating_type="reserved").count(),
        "total_capacity": Venue.objects.aggregate(total=Sum("capacity"))["total"] or 0,
    }

    context = {
        "venues": venues,
        "stats": stats,
        "can_manage": can_manage(role),
        "cities": Venue.objects.values_list("city", flat=True).distinct(),
    }
    return render(request, "venue_list.html", context)


def venue_create(request):
    role = _current_role(request)

    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa menambah venue.")
        return redirect(_with_role("events:venue_list", role))

    if request.method == "POST":
        form = VenueForm(request.POST)
        if form.is_valid():
            messages.success(request, "Venue berhasil ditambahkan.")
            return redirect(_with_role("events:venue_list", role))
    else:
        form = VenueForm()

    return render(request, "venue_form.html", {
        "form": form,
        "title": "Tambah Venue",
    })


def venue_update(request, pk):
    role = _current_role(request)

    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa mengubah venue.")
        return redirect(_with_role("events:venue_list", role))

    venue = get_object_or_404(Venue, pk=pk)

    if request.method == "POST":
        form = VenueForm(request.POST, instance=venue)
        if form.is_valid():
            messages.success(request, "Perubahan venue berhasil diproses.")
            return redirect(_with_role("events:venue_list", role))
    else:
        form = VenueForm(instance=venue)

    return render(request, "venue_form.html", {
        "form": form,
        "title": "Edit Venue",
    })


def venue_delete(request, pk):
    role = _current_role(request)

    if not can_manage(role):
        messages.error(request, "Hanya admin atau organizer yang bisa menghapus venue.")
        return redirect(_with_role("events:venue_list", role))

    venue = get_object_or_404(Venue, pk=pk)

    if request.method == "POST":
        messages.success(request, "Venue berhasil dihapus.")
        return redirect(_with_role("events:venue_list", role))

    return render(request, "venue_confirm_delete.html", {
        "venue": venue,
    })


def event_list(request):
    role = _current_role(request)
    events = Event.objects.select_related("venue", "organizer").prefetch_related("ticket_categories").all()

    q = request.GET.get("q", "")
    venue_id = request.GET.get("venue", "")
    artist = request.GET.get("artist", "")

    if q:
        events = events.filter(
            Q(event_title__icontains=q) |
            Q(artists__icontains=q)
        )

    if venue_id:
        events = events.filter(venue_id=venue_id)

    if artist:
        events = events.filter(artists__icontains=artist)

    context = {
        "events": events,
        "venues": Venue.objects.all(),
        "role": role,
    }
    return render(request, "event_list.html", context)


def event_manage_list(request):
    role = _current_role(request)

    if not can_manage(role):
        messages.error(request, "Halaman ini hanya untuk admin atau organizer.")
        return redirect(_with_role("dashboard", role))

    events = Event.objects.select_related("venue", "organizer").prefetch_related("ticket_categories")

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
        form = EventForm(request.POST)
        formset = TicketCategoryFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            messages.success(request, "Event berhasil dibuat.")
            return redirect(_with_role("events:event_manage_list", role))
    else:
        form = EventForm()
        formset = TicketCategoryFormSet()

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

    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        formset = TicketCategoryFormSet(request.POST, instance=event)

        if form.is_valid() and formset.is_valid():
            messages.success(request, "Event berhasil diperbarui.")
            return redirect(_with_role("events:event_manage_list", role))
    else:
        form = EventForm(instance=event)
        formset = TicketCategoryFormSet(instance=event)

    return render(request, "event_form.html", {
        "form": form,
        "formset": formset,
        "title": "Edit Event",
    })