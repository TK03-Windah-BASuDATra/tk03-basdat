from django.urls import path
from . import views

app_name = 'ticket_category'

urlpatterns = [
    path('',           views.ticket_category_list,   name='list'),
    path('create/',    views.ticket_category_create, name='create'),
    path('<int:pk>/data/',   views.ticket_category_data,   name='data'),
    path('<int:pk>/edit/',   views.ticket_category_edit,   name='edit'),
    path('<int:pk>/delete/', views.ticket_category_delete, name='delete'),
]