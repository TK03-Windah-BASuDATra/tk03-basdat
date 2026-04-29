from django.shortcuts import redirect, render

def dashboard(request):
    return render(request, "dashboard.html")


def _render_placeholder(request, title, description):
    return render(request, "placeholder_page.html", {
        "page_title": title,
        "page_description": description,
    })


def profile(request):
    return _render_placeholder(
        request,
        "Profile",
        "Halaman profile masih berupa placeholder untuk TK03."
    )


def manajemen_kursi(request):
    return _render_placeholder(
        request,
        "Manajemen Kursi",
        "Halaman manajemen kursi masih berupa placeholder untuk TK03."
    )


def kategori_tiket(request):
    return _render_placeholder(
        request,
        "Kategori Tiket",
        "Halaman kategori tiket masih berupa placeholder untuk TK03."
    )


def manajemen_tiket(request):
    return _render_placeholder(
        request,
        "Manajemen Tiket",
        "Halaman manajemen tiket masih berupa placeholder untuk TK03."
    )


def semua_order(request):
    return _render_placeholder(
        request,
        "Semua Order",
        "Halaman semua order masih berupa placeholder untuk TK03."
    )


def tiket_aset(request):
    return _render_placeholder(
        request,
        "Tiket (Aset)",
        "Halaman tiket aset masih berupa placeholder untuk TK03."
    )


def order_aset(request):
    return _render_placeholder(
        request,
        "Order (Aset)",
        "Halaman order aset masih berupa placeholder untuk TK03."
    )


def tiket_saya(request):
    return _render_placeholder(
        request,
        "Tiket Saya",
        "Halaman tiket saya masih berupa placeholder untuk TK03."
    )


def pesanan(request):
    return _render_placeholder(
        request,
        "Pesanan",
        "Halaman pesanan masih berupa placeholder untuk TK03."
    )


def promosi(request):
    return _render_placeholder(
        request,
        "Promosi",
        "Halaman promosi masih berupa placeholder untuk TK03."
    )


def artis(request):
    return _render_placeholder(
        request,
        "Artis",
        "Halaman artis masih berupa placeholder untuk TK03."
    )


def manajemen_venue(request):
    return redirect("venue_list")


def event_saya(request):
    return redirect("event_manage_list")


def cari_event(request):
    return redirect("event_list")


def venue(request):
    return redirect("venue_list")