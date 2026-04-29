from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.pilih_role_view, name="pilih_role"),
    path("register/<str:role>/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
]