from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/<uuid:event_id>/', views.checkout, name='checkout'),
    path('',                          views.order_list,  name='order_list'),
    path('semua/',                    views.order_list, name='semua_order'), # untuk Admin & Organizer
    path('pesanan/',                  views.order_list, name='pesanan'), # untuk Customer
]