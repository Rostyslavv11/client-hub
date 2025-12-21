from django.urls import path
from dashboard import views


app_name = "dashboard"

urlpatterns = [
    path("overview/", views.overview, name="overview"),
    path("find-talent/", views.find_talent, name="find_talent"),
]
