from django.urls import path
from .views import register_view
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
    path("login/", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="home"), name="logout"),
    path("register/",register_view, name="register"),
]

app_name = "accounts"