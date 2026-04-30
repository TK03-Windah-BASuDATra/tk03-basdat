from django.shortcuts import render
import uuid

def manajemen_tiket(request):
    user_role = request.GET.get('role', 'customer') or 'customer'
    if user_role not in ['admin', 'organizer', 'customer']:
        user_role = 'customer'

    # TODO: Replace w data dr db
    dummy_tickets = [
        {
            "id": "tkt_001",
            "code": "TIK-EVT001-VIP-001",
            "event": "Konser Melodi Senja",
            "event_id": "evt_001",
            "categories": ["VALID", "VIP"], 
            "datetime": "2024-05-15 19:00",
            "location": "Jakarta Convention Center",
            "price": 750000,
            "seat": "VIP B-1",
            "order_id": "ord_001",
            "customer": "Budi Santoso",
            "status": "Valid",
        },
        {
            "id": "tkt_002",
            "code": "TIK-EVT001-VIP-002",
            "event": "Konser Melodi Senja",
            "event_id": "evt_001",
            "categories": ["VALID", "VIP"],
            "datetime": "2024-05-15 19:00",
            "location": "Jakarta Convention Center",
            "price": 750000,
            "seat": "VIP B-2",
            "order_id": "ord_001",
            "customer": "Budi Santoso",
            "status": "Valid",
        },
        {
            "id": "tkt_003",
            "code": "TIK-EVT002-WVIP-001",
            "event": "Festival Musik 2026",
            "event_id": "evt_002",
            "categories": ["TERPAKAI", "WVIP"], 
            "datetime": "2024-06-20 18:30",
            "location": "Stadion Utama Gelora Bung Karno",
            "price": 1000000,
            "seat": "WVIP A-1",
            "order_id": "ord_002",
            "customer": "Siti Nurhaliza",
            "status": "Used",
        },
        {
            "id": "tkt_004",
            "code": "TIK-EVT001-REGULAR-001",
            "event": "Konser Melodi Senja",
            "event_id": "evt_001",
            "categories": ["VALID", "REGULAR"],
            "datetime": "2024-05-15 19:00",
            "location": "Jakarta Convention Center",
            "price": 350000,
            "seat": "-",
            "order_id": "ord_003",
            "customer": "Ahmad Wijaya",
            "status": "Valid",
        },
    ]

    # TODO: Replace w real available seats per event from db
    seats_by_event = {
        "evt_001": [
            {"seat_id": "seat_001", "label": "VIP — Baris B, No. 1", "available": True},
            {"seat_id": "seat_002", "label": "VIP — Baris B, No. 2", "available": True},
            {"seat_id": "seat_003", "label": "VIP — Baris B, No. 3", "available": False},
            {"seat_id": "seat_010", "label": "Regular — Bebas Duduk", "available": True},
        ],
        "evt_002": [
            {"seat_id": "seat_101", "label": "WVIP — Baris A, No. 1", "available": True},
            {"seat_id": "seat_102", "label": "WVIP — Baris A, No. 2", "available": True},
        ],
    }

    # TODO Replace w real orders from db
    orders = [
        {"order_id": "ord_001", "customer": "Budi Santoso", "event": "Konser Melodi Senja", "event_id": "evt_001"},
        {"order_id": "ord_002", "customer": "Siti Nurhaliza", "event": "Festival Musik 2026", "event_id": "evt_002"},
        {"order_id": "ord_003", "customer": "Ahmad Wijaya", "event": "Konser Melodi Senja", "event_id": "evt_001"},
    ]

    # TODO Replace w real ticket categories per event from db
    categories_by_event = {
        "evt_001": [
            {"category_id": "cat_001", "category_name": "VIP", "price": 750000, "used": 3, "quota": 150},
            {"category_id": "cat_002", "category_name": "Regular", "price": 350000, "used": 45, "quota": 200},
        ],
        "evt_002": [
            {"category_id": "cat_003", "category_name": "WVIP", "price": 1000000, "used": 10, "quota": 50},
            {"category_id": "cat_004", "category_name": "VIP", "price": 600000, "used": 25, "quota": 100},
        ],
    }
    
    # TODO: count from db
    total_tickets = len(dummy_tickets)
    valid_tickets = sum(1 for t in dummy_tickets if t["status"] == "Valid")
    used_tickets = sum(1 for t in dummy_tickets if t["status"] == "Used")
    
    # TODO: filter depend on role
    # if user_role == 'customer':
    #     filtered_tickets = [t for t in dummy_tickets if t["customer"] == request.user.customer.name]
    #     page_title = "Tiket Saya"
    # elif user_role in ['admin', 'organizer']:
    #     filtered_tickets = dummy_tickets
    #     page_title = "Manajemen Tiket"
    
    filtered_tickets = dummy_tickets
    page_title = "Manajemen Tiket" if user_role in ['admin', 'organizer'] else "Tiket Saya"
    show_add_button = user_role in ['admin', 'organizer']
    show_customer_column = user_role in ['admin', 'organizer']
    can_admin_actions = user_role == 'admin'
    
    context = {
        "page_title": page_title,
        "tickets": filtered_tickets,
        "total_tickets": total_tickets,
        "valid_tickets": valid_tickets,
        "used_tickets": used_tickets,
        "show_add_button": show_add_button,
        "show_customer_column": show_customer_column,
        "user_role": user_role,
        "seats_by_event": seats_by_event,
        "can_admin_actions": can_admin_actions,
        "orders": orders,
        "categories_by_event": categories_by_event,
    }
    
    return render(request, "manajemen_tiket.html", context)
