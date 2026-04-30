# orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/<uuid:event_id>/', views.checkout,   name='checkout'),
    path('semua/',                   views.order_list, name='semua_order'),
    path('pesanan/',                 views.order_list, name='pesanan'),
    path('update/<uuid:order_id>/',   views.order_update, name='order_update'),  
    path('delete/<uuid:order_id>/',   views.order_delete, name='order_delete'),  
    path('promosi/',                         views.promotion_list,    name='promosi'),        # ← fitur 17, dibuat nanti
    path('promosi/create/',                  views.promotion_create,  name='promotion_create'),
    path('promosi/update/<uuid:promotion_id>/', views.promotion_update, name='promotion_update'),
    path('promosi/delete/<uuid:promotion_id>/', views.promotion_delete, name='promotion_delete'),
]