from django.urls import path
from .views import register_choice, register_client, register_freelancer, login_view, logout_view


urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register_choice, name="register"),
    path("register/client/", register_client, name="register_client"),
    path("register/freelancer/", register_freelancer, name="register_freelancer"),
]

app_name = "accounts"
