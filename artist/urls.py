from django.urls import path
from . import views

app_name = 'artist'

urlpatterns = [
    path('', views.artist_list, name='list'),
    path('create/', views.artist_create, name='create'),
    path('<uuid:pk>/data/', views.artist_data, name='data'),
    path('<uuid:pk>/edit/', views.artist_edit, name='edit'),
    path('<uuid:pk>/delete/', views.artist_delete, name='delete'),
    path('add-to-event/', views.add_to_event_page, name='add_to_event_page'),  # GET → halaman
    path('add-to-event/submit/', views.artist_add_to_event, name='add_to_event'),  # POST → action
]