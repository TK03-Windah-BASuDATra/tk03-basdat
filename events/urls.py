from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('venues/', views.venue_list, name='venue_list'),
    path('venues/create/', views.venue_create, name='venue_create'),
    path('venues/<uuid:pk>/edit/', views.venue_update, name='venue_update'),
    path('venues/<uuid:pk>/delete/', views.venue_delete, name='venue_delete'),

    path('my-events/', views.event_manage_list, name='event_manage_list'),
    path('create/', views.event_create, name='event_create'),
    path('<uuid:pk>/edit/', views.event_update, name='event_update'),
]