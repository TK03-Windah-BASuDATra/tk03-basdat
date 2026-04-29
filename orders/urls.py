# orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/<str:event_id>/', views.checkout,   name='checkout'),
    path('semua/',                   views.order_list, name='semua_order'),
    path('pesanan/',                 views.order_list, name='pesanan'),
]