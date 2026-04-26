from django.shortcuts import render

def dashboard(request):
    return render(request, "dashboard.html")

def profile(request):
    return render(request, "profile.html")

def manajemen_venue(request):
    return render(request, "manajemen_venue.html")

def manajemen_kursi(request):
    return render(request, "manajemen_kursi.html")

def kategori_tiket(request):
    return render(request, "kategori_tiket.html")

def manajemen_tiket(request):
    return render(request, "manajemen_tiket.html")

def semua_order(request):
    return render(request, "semua_order.html")

def tiket_aset(request):
    return render(request, "tiket_aset.html")

def order_aset(request):
    return render(request, "order_aset.html")

def event_saya(request):
    return render(request, "event_saya.html")

def tiket_saya(request):
    return render(request, "tiket_saya.html")

def pesanan(request):
    return render(request, "pesanan.html")

def cari_event(request):
    return render(request, "cari_event.html")

def promosi(request):
    return render(request, "promosi.html")

def venue(request):
    return render(request, "venue.html")

def artis(request):
    return render(request, "artis.html")