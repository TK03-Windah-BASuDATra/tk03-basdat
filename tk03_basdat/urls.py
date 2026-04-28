from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    
    path("accounts/", include("accounts.urls")),
    path('events/', include('events.urls')),

    path("profile/", views.profile, name="profile"),

    path("manajemen-venue/", views.manajemen_venue, name="manajemen_venue"),
    path("manajemen-kursi/", views.manajemen_kursi, name="manajemen_kursi"),
    path("kategori-tiket/", views.kategori_tiket, name="kategori_tiket"),
    path("manajemen-tiket/", views.manajemen_tiket, name="manajemen_tiket"),
    path("semua-order/", views.semua_order, name="semua_order"),
    path("tiket-aset/", views.tiket_aset, name="tiket_aset"),
    path("order-aset/", views.order_aset, name="order_aset"),

    path("event-saya/", views.event_saya, name="event_saya"),

    path("tiket-saya/", views.tiket_saya, name="tiket_saya"),
    path("pesanan/", views.pesanan, name="pesanan"),
    path("cari-event/", views.cari_event, name="cari_event"),
    path("promosi/", views.promosi, name="promosi"),
    path("venue/", views.venue, name="venue"),
    path("artis/", views.artis, name="artis"),
    path('orders/',   include('orders.urls')),
]