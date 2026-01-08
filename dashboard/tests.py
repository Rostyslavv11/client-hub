from datetime import date, timedelta

from django.core import mail, signing
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Category, ClientProfile, FreelancerProfile
from messages_app.models import Conversation, Message, Notification
from projects.models import Application, Project
from dashboard.views import EMAIL_VERIFICATION_SALT


class DashboardTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()

    def _create_client(self, email="client@example.com"):
        user = self.user_model.objects.create_user(
            email=email,
            password="Pass12345!",
            first_name="Client",
            last_name="User",
            role="client",
        )
        ClientProfile.objects.create(user=user, company_name="Acme")
        return user

    def _create_freelancer(self, email="freelancer@example.com"):
        user = self.user_model.objects.create_user(
            email=email,
            password="Pass12345!",
            first_name="Freelancer",
            last_name="User",
            role="freelancer",
        )
        FreelancerProfile.objects.create(user=user, title="Dev", hourly_rate=50)
        return user

    def _create_project(self, client_user, status=Project.Status.OPEN):
        return Project.objects.create(
            client=client_user.client_profile,
            created_by=client_user,
            title="Test project",
            description="Project description",
            project_overview="Overview",
            responsibilities="Do things",
            requirements="Know things",
            deadline=date.today() + timedelta(days=7),
            status=status,
            status_of_publishing=Project.PublishingStatus.LAUNCHED,
        )

    def test_profile_creates_freelancer_profile_defaults(self):
        user = self.user_model.objects.create_user(
            email="newfreelancer@example.com",
            password="Pass12345!",
            first_name="New",
            last_name="Freelancer",
            role="freelancer",
        )
        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.get(reverse("dashboard:profile"))

        self.assertEqual(response.status_code, 200)
        profile = FreelancerProfile.objects.get(user=user)
        self.assertEqual(profile.title, "Freelancer")
        self.assertEqual(profile.hourly_rate, 0)

    def test_find_talent_list_shows_only_freelancers(self):
        client_user = self._create_client()
        freelancer_user = self._create_freelancer()
        self.client.login(username=client_user.email, password="Pass12345!")

        response = self.client.get(reverse("dashboard:find_talent"))
        freelancers = list(response.context["freelancers"])

        self.assertEqual(response.status_code, 200)
        self.assertIn(freelancer_user.freelancer_profile, freelancers)
        self.assertNotIn(client_user, freelancers)

    def test_find_talent_filters_by_category_and_rate(self):
        client_user = self._create_client(email="client2@example.com")
        category = Category.objects.create(code="design", name="Design")
        match_user = self._create_freelancer(email="match@example.com")
        match_user.category.add(category)
        match_user.freelancer_profile.hourly_rate = 30
        match_user.freelancer_profile.save(update_fields=["hourly_rate"])
        other_user = self._create_freelancer(email="other@example.com")
        other_user.freelancer_profile.hourly_rate = 120
        other_user.freelancer_profile.save(update_fields=["hourly_rate"])

        self.client.login(username=client_user.email, password="Pass12345!")
        response = self.client.get(
            reverse("dashboard:find_talent"),
            data={"category": category.id, "rate": "25-50"},
        )

        freelancers = list(response.context["freelancers"])
        self.assertIn(match_user.freelancer_profile, freelancers)
        self.assertNotIn(other_user.freelancer_profile, freelancers)

    def test_find_talent_searches_by_name(self):
        client_user = self._create_client(email="client3@example.com")
        john_user = self._create_freelancer(email="john@example.com")
        john_user.first_name = "John"
        john_user.last_name = "Smith"
        john_user.save(update_fields=["first_name", "last_name"])
        self._create_freelancer(email="jane@example.com")

        self.client.login(username=client_user.email, password="Pass12345!")
        response = self.client.get(
            reverse("dashboard:find_talent"),
            data={"q": "John"},
        )

        freelancers = list(response.context["freelancers"])
        self.assertIn(john_user.freelancer_profile, freelancers)

    def test_messages_view_marks_unread_items(self):
        client_user = self._create_client()
        freelancer_user = self._create_freelancer()
        project = self._create_project(client_user)
        conversation = Conversation.objects.create(
            project=project,
            client=client_user,
            freelancer=freelancer_user,
        )
        message = Message.objects.create(
            conversation=conversation,
            sender=freelancer_user,
            body="Hello",
        )
        notification = Notification.objects.create(
            user=client_user,
            actor=freelancer_user,
            conversation=conversation,
            kind=Notification.Kind.MESSAGE,
            title="New message",
            body="Hello",
        )

        self.client.login(username=client_user.email, password="Pass12345!")
        response = self.client.get(
            f"{reverse('dashboard:messages')}?conversation={conversation.id}"
        )

        message.refresh_from_db()
        notification.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(message.is_read)
        self.assertTrue(notification.is_read)

    def test_decide_application_accept_updates_project_status(self):
        client_user = self._create_client()
        freelancer_user = self._create_freelancer()
        project = self._create_project(client_user)
        application = Application.objects.create(
            project=project,
            freelancer=freelancer_user,
            full_name="Freelancer User",
            email="freelancer@example.com",
            status=Application.Status.IN_REVIEW,
        )

        self.client.login(username=client_user.email, password="Pass12345!")
        response = self.client.post(
            reverse("dashboard:decide_application", args=[application.id]),
            data={"action": "accept"},
        )

        application.refresh_from_db()
        project.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(application.status, Application.Status.IN_PROGRESS)
        self.assertEqual(project.status, Project.Status.IN_PROGRESS)

    def test_decide_application_complete_updates_project_status(self):
        client_user = self._create_client()
        freelancer_user = self._create_freelancer()
        project = self._create_project(client_user, status=Project.Status.IN_PROGRESS)
        application = Application.objects.create(
            project=project,
            freelancer=freelancer_user,
            full_name="Freelancer User",
            email="freelancer@example.com",
            status=Application.Status.IN_PROGRESS,
        )

        self.client.login(username=client_user.email, password="Pass12345!")
        response = self.client.post(
            reverse("dashboard:decide_application", args=[application.id]),
            data={"action": "complete"},
        )

        application.refresh_from_db()
        project.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(application.status, Application.Status.COMPLETED)
        self.assertEqual(project.status, Project.Status.COMPLETED)

    def test_decide_application_rejects_non_owner(self):
        client_user = self._create_client()
        freelancer_user = self._create_freelancer()
        project = self._create_project(client_user)
        application = Application.objects.create(
            project=project,
            freelancer=freelancer_user,
            full_name="Freelancer User",
            email="freelancer@example.com",
            status=Application.Status.IN_REVIEW,
        )

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.post(
            reverse("dashboard:decide_application", args=[application.id]),
            data={"action": "accept"},
        )

        application.refresh_from_db()
        project.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(application.status, Application.Status.IN_REVIEW)
        self.assertEqual(project.status, Project.Status.OPEN)

    def test_decide_application_rejects_invalid_action(self):
        client_user = self._create_client(email="invalidaction@example.com")
        freelancer_user = self._create_freelancer(email="invalidfreelancer@example.com")
        project = self._create_project(client_user)
        application = Application.objects.create(
            project=project,
            freelancer=freelancer_user,
            full_name="Freelancer User",
            email="invalidfreelancer@example.com",
            status=Application.Status.IN_REVIEW,
        )

        self.client.login(username=client_user.email, password="Pass12345!")
        response = self.client.post(
            reverse("dashboard:decide_application", args=[application.id]),
            data={"action": "unknown"},
        )

        application.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(application.status, Application.Status.IN_REVIEW)

    def test_decide_application_complete_requires_in_progress(self):
        client_user = self._create_client(email="completeguard@example.com")
        freelancer_user = self._create_freelancer(email="completefreelancer@example.com")
        project = self._create_project(client_user)
        application = Application.objects.create(
            project=project,
            freelancer=freelancer_user,
            full_name="Freelancer User",
            email="completefreelancer@example.com",
            status=Application.Status.IN_REVIEW,
        )

        self.client.login(username=client_user.email, password="Pass12345!")
        response = self.client.post(
            reverse("dashboard:decide_application", args=[application.id]),
            data={"action": "complete"},
        )

        application.refresh_from_db()
        project.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(application.status, Application.Status.IN_REVIEW)
        self.assertEqual(project.status, Project.Status.OPEN)

    def test_profile_email_and_phone_change_resets_verification(self):
        user = self._create_freelancer(email="verify@example.com")
        user.email_verified = True
        user.phone_verified = True
        user.email_verification_sent_at = timezone.now()
        user.phone_verification_sent_at = timezone.now()
        user.phone_verification_code = "123456"
        user.save()

        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.post(
            reverse("dashboard:profile"),
            data={
                "profile_submit": "1",
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": "newverify@example.com",
                "phone_number": "1234567890",
                "title": "Developer",
                "hourly_rate": "25",
                "bio": "",
                "location": "Test City",
                "weekly_capacity": "40",
                "portfolio_website": "",
            },
        )

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(user.email_verified)
        self.assertIsNone(user.email_verification_sent_at)
        self.assertFalse(user.phone_verified)
        self.assertIsNone(user.phone_verification_sent_at)
        self.assertEqual(user.phone_verification_code, "")

    def test_profile_password_change_keeps_session(self):
        user = self._create_freelancer(email="password@example.com")
        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.post(
            reverse("dashboard:profile"),
            data={
                "password_submit": "1",
                "old_password": "Pass12345!",
                "new_password1": "Newpass123!",
                "new_password2": "Newpass123!",
            },
            follow=True,
        )

        user.refresh_from_db()
        self.assertTrue(user.check_password("Newpass123!"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_client_projects_for_non_client_returns_empty(self):
        freelancer_user = self._create_freelancer(email="projectsfreelancer@example.com")
        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.get(reverse("dashboard:client_projects"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["projects_total"], 0)
        self.assertEqual(response.context["projects"], [])

    def test_client_hired_freelancers_for_non_client_empty(self):
        freelancer_user = self._create_freelancer(email="hiredfreelancer@example.com")
        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.get(reverse("dashboard:client_hired_freelancers"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_applications"], 0)
        self.assertEqual(response.context["results_count"], 0)

    def test_client_notes_create_and_delete(self):
        client_user = self._create_client(email="notes@example.com")
        self.client.login(username=client_user.email, password="Pass12345!")
        create_response = self.client.post(
            reverse("dashboard:client_notes_create"),
            data={"title": "Note title", "body": "Note body"},
        )

        self.assertEqual(create_response.status_code, 200)
        note_id = create_response.json()["id"]
        delete_response = self.client.post(
            reverse("dashboard:client_notes_delete", args=[note_id])
        )

        self.assertEqual(delete_response.status_code, 200)

    def test_client_notes_create_requires_client(self):
        freelancer_user = self._create_freelancer(email="notesfreelancer@example.com")
        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.post(
            reverse("dashboard:client_notes_create"),
            data={"title": "Nope", "body": "Nope"},
        )

        self.assertEqual(response.status_code, 403)

    def test_client_notes_delete_requires_owner(self):
        client_user = self._create_client(email="ownerclient@example.com")
        other_user = self._create_client(email="otherclient@example.com")
        self.client.login(username=client_user.email, password="Pass12345!")
        create_response = self.client.post(
            reverse("dashboard:client_notes_create"),
            data={"title": "Note title", "body": "Note body"},
        )
        note_id = create_response.json()["id"]

        self.client.logout()
        self.client.login(username=other_user.email, password="Pass12345!")
        delete_response = self.client.post(
            reverse("dashboard:client_notes_delete", args=[note_id])
        )

        self.assertEqual(delete_response.status_code, 404)

    def test_send_email_verification_sends_email(self):
        user = self._create_freelancer(email="emailverify@example.com")
        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.post(reverse("dashboard:send_email_verification"))

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(user.email_verification_sent_at)
        self.assertEqual(len(mail.outbox), 1)

    def test_verify_email_marks_verified(self):
        user = self._create_freelancer(email="verifytoken@example.com")
        token = signing.dumps(
            {"user_id": user.pk, "email": user.email},
            salt=EMAIL_VERIFICATION_SALT,
        )
        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.get(reverse("dashboard:verify_email", args=[token]))

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(user.email_verified)

    def test_verify_email_invalid_token_redirects(self):
        user = self._create_freelancer(email="badtoken@example.com")
        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.get(reverse("dashboard:verify_email", args=["badtoken"]))

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(user.email_verified)

    def test_send_phone_verification_sets_code(self):
        user = self._create_freelancer(email="phoneverify@example.com")
        user.phone_number = "1234567890"
        user.save(update_fields=["phone_number"])
        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.post(reverse("dashboard:send_phone_verification"))

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(user.phone_verification_code)
        self.assertEqual(len(user.phone_verification_code), 6)
        self.assertIsNotNone(user.phone_verification_sent_at)

    def test_send_phone_verification_requires_number(self):
        user = self._create_freelancer(email="phonereq@example.com")
        user.phone_number = ""
        user.save(update_fields=["phone_number"])
        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.post(reverse("dashboard:send_phone_verification"))

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(user.phone_verification_code, "")

    def test_verify_phone_marks_verified(self):
        user = self._create_freelancer(email="phonecode@example.com")
        user.phone_verification_code = "123456"
        user.phone_verification_sent_at = timezone.now()
        user.save(update_fields=["phone_verification_code", "phone_verification_sent_at"])

        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.post(
            reverse("dashboard:verify_phone"),
            data={"phone_code": "123456"},
        )

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(user.phone_verified)
        self.assertEqual(user.phone_verification_code, "")
        self.assertIsNone(user.phone_verification_sent_at)

    def test_verify_phone_rejects_wrong_code(self):
        user = self._create_freelancer(email="phonewrong@example.com")
        user.phone_verification_code = "123456"
        user.phone_verification_sent_at = timezone.now()
        user.save(update_fields=["phone_verification_code", "phone_verification_sent_at"])

        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.post(
            reverse("dashboard:verify_phone"),
            data={"phone_code": "000000"},
        )

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(user.phone_verified)
        self.assertEqual(user.phone_verification_code, "123456")

    def test_find_talent_sort_rate_desc(self):
        client_user = self._create_client(email="sortclient@example.com")
        higher = self._create_freelancer(email="higher@example.com")
        higher.freelancer_profile.hourly_rate = 100
        higher.freelancer_profile.save(update_fields=["hourly_rate"])
        lower = self._create_freelancer(email="lower@example.com")
        lower.freelancer_profile.hourly_rate = 20
        lower.freelancer_profile.save(update_fields=["hourly_rate"])

        self.client.login(username=client_user.email, password="Pass12345!")
        response = self.client.get(
            reverse("dashboard:find_talent"),
            data={"sort": "rate_desc"},
        )

        freelancers = list(response.context["freelancers"])
        self.assertEqual(freelancers[0].user_id, higher.id)

    def test_find_talent_sort_name(self):
        client_user = self._create_client(email="sortnameclient@example.com")
        alpha = self._create_freelancer(email="alpha@example.com")
        alpha.first_name = "Alpha"
        alpha.save(update_fields=["first_name"])
        beta = self._create_freelancer(email="beta@example.com")
        beta.first_name = "Beta"
        beta.save(update_fields=["first_name"])

        self.client.login(username=client_user.email, password="Pass12345!")
        response = self.client.get(
            reverse("dashboard:find_talent"),
            data={"sort": "name"},
        )

        freelancers = list(response.context["freelancers"])
        self.assertEqual(freelancers[0].user_id, alpha.id)
