from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.manajemen_tiket, name='my-tickets'),
    path('create/', views.ticket_create, name='ticket_create'),
    path('update/<str:ticket_id>/', views.ticket_update, name='ticket_update'),
    path('delete/<str:ticket_id>/', views.ticket_delete, name='ticket_delete'),
]
