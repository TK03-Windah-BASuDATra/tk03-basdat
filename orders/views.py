import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from events.models import Event, TicketCategory, Promotion
from accounts.models import Customer
from .models import Order, Ticket, HasRelationship, OrderPromotion
from .forms import CheckoutForm


@login_required
def checkout(request, event_id):
    """Halaman checkout tiket untuk Customer."""
    # Hanya Customer yang boleh akses
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        messages.error(request, 'Hanya Customer yang dapat membeli tiket.')
        return redirect('events:event_list')

    event = get_object_or_404(Event, pk=event_id)
    form  = CheckoutForm(event=event)

    # Hitung preview total (untuk ringkasan pesanan di sidebar)
    preview_total = 0
    selected_category = None
    selected_quantity = 1
    promo_error = None

    if request.method == 'POST':
        form = CheckoutForm(event=event, data=request.POST)

        # Jika tombol "Terapkan" promo ditekan — hanya validasi promo, tidak submit order
        if 'apply_promo' in request.POST:
            # Re-render dengan pesan validasi promo dari form.clean
            form.is_valid()  # trigger validation so promo error appears
            return render(request, 'orders/checkout.html', {
                'event': event,
                'form': form,
            })

        # Tombol "Bayar Sekarang"
        if form.is_valid():
            cd        = form.cleaned_data
            category  = cd['category']
            quantity  = cd['quantity']
            seats     = cd.get('seats')
            promo_obj = cd.get('promo_obj')

            # --- Hitung total ---
            base_total = category.price * quantity
            discount   = 0
            if promo_obj:
                if promo_obj.discount_type == 'PERCENTAGE':
                    discount = base_total * (promo_obj.discount_value / 100)
                else:  # NOMINAL
                    discount = promo_obj.discount_value
            total = max(base_total - discount, 0)

            # --- Buat Order ---
            order = Order.objects.create(
                order_date=timezone.now(),
                payment_status='Pending',
                total_amount=total,
                customer=customer,
            )

            # --- Buat Ticket(s) ---
            tickets_created = []
            for i in range(quantity):
                code   = f'TKT-{uuid.uuid4().hex[:8].upper()}'
                ticket = Ticket.objects.create(
                    ticket_code=code,
                    category=category,
                    order=order,
                )
                tickets_created.append(ticket)

            # --- Assign kursi (jika dipilih) ---
            if seats:
                for seat, ticket in zip(seats, tickets_created):
                    HasRelationship.objects.create(seat=seat, ticket=ticket)

            # --- Simpan promo ---
            if promo_obj:
                OrderPromotion.objects.create(promotion=promo_obj, order=order)

            # --- Kurangi quota ---
            category.quota -= quantity
            category.save()

            messages.success(request, f'Pesanan berhasil dibuat! Order ID: {order.order_id}')
            return redirect('orders:order_list')

    return render(request, 'orders/checkout.html', {
        'event': event,
        'form': form,
    })