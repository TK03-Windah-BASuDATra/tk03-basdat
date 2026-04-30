from django.urls import path
from . import views

app_name = 'seats'

urlpatterns = [
    path('', views.manajemen_kursi, name='manajemen_kursi'),
]
