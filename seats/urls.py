from django.urls import path
from django.urls import path
from . import views

urlpatterns = [
    path('', views.manajemen_kursi, name='manajemen_kursi'),
]
