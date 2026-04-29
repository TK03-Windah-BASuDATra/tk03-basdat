from django.urls import path
from . import views

urlpatterns = [
    path('', views.manajemen_tiket, name='manajemen_tiket'),
]
