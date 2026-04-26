from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EventForm, TicketCategoryFormSet, VenueForm
from .models import Event, Venue


def can_manage(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser or getattr(user, 'role', '') == 'organizer')


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def venue_list(request):
    venues = Venue.objects.all()

    q = request.GET.get('q', '')
    city = request.GET.get('city', '')
    seating = request.GET.get('seating', '')

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
        'total_venue': Venue.objects.count(),
        'reserved_count': Venue.objects.filter(seating_type='reserved').count(),
        'total_capacity': Venue.objects.aggregate(total=Sum('capacity'))['total'] or 0,
    }

    context = {
        'venues': venues,
        'stats': stats,
        'can_manage': can_manage(request.user),
        'cities': Venue.objects.values_list('city', flat=True).distinct(),
    }
    return render(request, 'events/venue_list.html', context)


@login_required
@user_passes_test(can_manage)
def venue_create(request):
    if request.method == 'POST':
        form = VenueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venue berhasil ditambahkan.')
            return redirect('venue_list')
    else:
        form = VenueForm()

    return render(request, 'events/venue_form.html', {
        'form': form,
        'title': 'Tambah Venue'
    })


@login_required
@user_passes_test(can_manage)
def venue_update(request, pk):
    venue = get_object_or_404(Venue, pk=pk)

    if request.method == 'POST':
        form = VenueForm(request.POST, instance=venue)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venue berhasil diperbarui.')
            return redirect('venue_list')
    else:
        form = VenueForm(instance=venue)

    return render(request, 'events/venue_form.html', {
        'form': form,
        'title': 'Edit Venue'
    })


@login_required
@user_passes_test(can_manage)
def venue_delete(request, pk):
    venue = get_object_or_404(Venue, pk=pk)

    if request.method == 'POST':
        venue.delete()
        messages.success(request, 'Venue berhasil dihapus.')
        return redirect('venue_list')

    return render(request, 'events/venue_confirm_delete.html', {'venue': venue})


def event_list(request):
    events = Event.objects.select_related('venue', 'organizer').prefetch_related('ticket_categories').all()

    q = request.GET.get('q', '')
    venue_id = request.GET.get('venue', '')
    artist = request.GET.get('artist', '')

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
        'events': events,
        'venues': Venue.objects.all(),
    }
    return render(request, 'events/event_list.html', context)


@login_required
@user_passes_test(can_manage)
def event_manage_list(request):
    events = Event.objects.select_related('venue', 'organizer').prefetch_related('ticket_categories')

    if not is_admin(request.user):
        events = events.filter(organizer=request.user)

    context = {
        'events': events,
    }
    return render(request, 'events/event_manage_list.html', context)


@login_required
@user_passes_test(can_manage)
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        formset = TicketCategoryFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()

            formset.instance = event
            formset.save()

            messages.success(request, 'Event berhasil dibuat.')
            return redirect('event_manage_list')
    else:
        form = EventForm()
        formset = TicketCategoryFormSet()

    return render(request, 'events/event_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Buat Event'
    })


@login_required
@user_passes_test(can_manage)
def event_update(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if not is_admin(request.user) and event.organizer != request.user:
        messages.error(request, 'Kamu tidak punya akses untuk mengubah event ini.')
        return redirect('event_manage_list')

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        formset = TicketCategoryFormSet(request.POST, instance=event)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Event berhasil diperbarui.')
            return redirect('event_manage_list')
    else:
        form = EventForm(instance=event)
        formset = TicketCategoryFormSet(instance=event)

    return render(request, 'events/event_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Edit Event'
    })