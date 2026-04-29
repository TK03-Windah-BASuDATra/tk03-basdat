from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("main.urls")),
    path('artist/', include('artist.urls')),
    path('ticket-category/', include('ticket_category.urls')),
    path("accounts/", include("accounts.urls")),
    path('events/', include('events.urls')),
    path('orders/', include('orders.urls')),
]

