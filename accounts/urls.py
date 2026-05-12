from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("tambah-role/", views.add_role_view, name="add_role"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/update/", views.profile_update, name="profile_update"),
    path("profile/password/", views.profile_password, name="profile_password"),
]