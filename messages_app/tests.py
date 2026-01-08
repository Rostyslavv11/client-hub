from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from messages_app.models import Notification


class NotificationTests(TestCase):
    def test_mark_notifications_read(self):
        user = get_user_model().objects.create_user(
            email="notify@example.com",
            password="Pass12345!",
            first_name="Notify",
            last_name="User",
        )
        Notification.objects.create(
            user=user,
            kind=Notification.Kind.MESSAGE,
            title="Hello",
            body="Test",
        )

        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.post(reverse("messages_app:notifications_mark_read"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Notification.objects.filter(user=user, is_read=False).count() == 0
        )

    def test_mark_notifications_read_requires_login(self):
        response = self.client.post(reverse("messages_app:notifications_mark_read"))

        self.assertEqual(response.status_code, 302)

    def test_mark_notifications_read_requires_post(self):
        user = get_user_model().objects.create_user(
            email="postonly@example.com",
            password="Pass12345!",
            first_name="Post",
            last_name="Only",
        )
        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.get(reverse("messages_app:notifications_mark_read"))

        self.assertEqual(response.status_code, 405)
