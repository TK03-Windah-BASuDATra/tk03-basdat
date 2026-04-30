from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.manajemen_tiket, name='my-tickets'),
]
