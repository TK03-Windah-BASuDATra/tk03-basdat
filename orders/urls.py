from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/<uuid:event_id>/', views.checkout, name='checkout'),
]