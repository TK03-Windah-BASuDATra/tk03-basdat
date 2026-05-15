from django.urls import path
from . import views

app_name = 'seats'

urlpatterns = [
    path('', views.manajemen_kursi, name='manajemen_kursi'),
    path('create/', views.seat_create, name='seat_create'),
    path('update/<str:seat_id>/', views.seat_update, name='seat_update'),
    path('delete/<str:seat_id>/', views.seat_delete, name='seat_delete'),
]
