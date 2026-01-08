from django.urls import path

from . import views

app_name = "messages_app"

urlpatterns = [
    path("notifications/mark-read/", views.mark_notifications_read, name="notifications_mark_read"),
]
