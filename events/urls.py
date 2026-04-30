from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("venues/", views.venue_list, name="venue_list"),
    path("venues/create/", views.venue_create, name="venue_create"),
    path("venues/edit/", views.venue_update, name="venue_update"),
    path("venues/delete/", views.venue_delete, name="venue_delete"),

    path("events/", views.event_list, name="event_list"),
    path("my-events/", views.event_manage_list, name="event_manage_list"),
    path("events/create/", views.event_create, name="event_create"),
    path("events/edit/", views.event_update, name="event_update"),
    path("events/delete/", views.event_delete, name="event_delete"),
]