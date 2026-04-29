# orders/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def checkout(request, event_id):
    """Halaman checkout tiket - data dummy untuk frontend."""

    # Data dummy event
    event = {
        'event_id':       event_id,
        'event_title':    'Konser Melodi Senja',
        'event_datetime': '2024-05-15 19:00',
        'venue_name':     'Jakarta Convention Center',
        'artists':        ['Fourtwnty', 'Hindia'],
    }

    # Data dummy kategori tiket
    categories = [
        {'id': 1, 'name': 'WVIP',       'quota': 50,  'price': 1500000},
        {'id': 2, 'name': 'VIP',        'quota': 150, 'price': 750000},
        {'id': 3, 'name': 'Category 1', 'quota': 300, 'price': 450000},
        {'id': 4, 'name': 'Category 2', 'quota': 500, 'price': 250000},
    ]

    # Data dummy kursi
    seats = ['A1','A2','A3','A4','A5','B1','B2','B3','B4','B5','C1','C2']

    # Simulasi POST (Terapkan promo / Bayar)
    promo_error   = None
    promo_success = None
    selected_cat  = None
    quantity      = 1

    if request.method == 'POST':
        if 'apply_promo' in request.POST:
            promo_code = request.POST.get('promo_code', '').strip()
            if promo_code == 'TIKTAK20':
                promo_success = f'Promo "{promo_code}" berhasil diterapkan! Diskon 20%.'
            else:
                promo_error = 'Kode promo tidak valid.'

        elif 'place_order' in request.POST:
            messages.success(request, 'Pesanan berhasil dibuat!')
            return redirect('pesanan')

    context = {
        'event':         event,
        'categories':    categories,
        'seats':         seats,
        'promo_error':   promo_error,
        'promo_success': promo_success,
        'quantity':      quantity,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_list(request):
    """Halaman daftar order - data dummy untuk frontend."""

    user = request.user
    role = getattr(user, 'role', 'customer')

    # Data dummy orders
    all_orders = [
        {
            'order_id':       'ord_001',
            'order_date':     '2024-04-10 14:32',
            'payment_status': 'Paid',
            'total_amount':   1200000,
            'customer_name':  'Budi Santoso',
            'customer_initial': 'B',
        },
        {
            'order_id':       'ord_002',
            'order_date':     '2024-04-11 09:15',
            'payment_status': 'Paid',
            'total_amount':   150000,
            'customer_name':  'Budi Santoso',
            'customer_initial': 'B',
        },
        {
            'order_id':       'ord_003',
            'order_date':     '2024-04-12 18:44',
            'payment_status': 'Pending',
            'total_amount':   1500000,
            'customer_name':  'Siti Rahayu',
            'customer_initial': 'S',
        },
        {
            'order_id':       'ord_004',
            'order_date':     '2024-04-13 11:00',
            'payment_status': 'Cancelled',
            'total_amount':   700000,
            'customer_name':  'Siti Rahayu',
            'customer_initial': 'S',
        },
    ]

    # Filter sesuai role
    if role == 'customer':
        # Customer hanya lihat miliknya sendiri (dummy: ambil 2 pertama)
        orders = all_orders[:2]
    else:
        # Admin & Organizer lihat semua
        orders = all_orders

    # Filter pencarian & status dari GET
    search_query  = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    if search_query:
        orders = [o for o in orders if search_query.lower() in o['order_id'].lower()]

    if status_filter:
        orders = [o for o in orders if o['payment_status'] == status_filter]

    # Statistik ringkasan
    total_order   = len(orders)
    total_paid    = sum(1 for o in orders if o['payment_status'] == 'Paid')
    total_pending = sum(1 for o in orders if o['payment_status'] == 'Pending')
    total_revenue = sum(o['total_amount'] for o in orders if o['payment_status'] == 'Paid')

    context = {
        'orders':        orders,
        'role':          role,
        'is_admin':      role == 'admin' or user.is_superuser,
        'is_organizer':  role == 'organizer',
        'is_customer':   role == 'customer',
        'search_query':  search_query,
        'status_filter': status_filter,
        'total_order':   total_order,
        'total_paid':    total_paid,
        'total_pending': total_pending,
        'total_revenue': total_revenue,
        'status_choices': [
            ('Paid',      'Lunas'),
            ('Pending',   'Pending'),
            ('Cancelled', 'Dibatalkan'),
        ],
    }
    return render(request, 'orders/order_list.html', context)