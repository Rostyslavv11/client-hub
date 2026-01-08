from datetime import date, timedelta

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import ClientProfile, FreelancerProfile
from messages_app.models import Message, Notification
from projects.forms import ApplicationForm
from projects.models import (
    Application,
    Invitation,
    Project,
    ProjectAttachment,
    SavedProject,
    Tags,
)


class ProjectFlowTests(TestCase):
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

    def _create_project(self, client_user, status, publishing):
        return Project.objects.create(
            client=client_user.client_profile,
            created_by=client_user,
            title=f"{status} project",
            description="Project description",
            project_overview="Overview",
            responsibilities="Do things",
            requirements="Know things",
            deadline=date.today() + timedelta(days=7),
            status=status,
            status_of_publishing=publishing,
        )

    def test_find_work_only_shows_open_launched_projects(self):
        freelancer_user = self._create_freelancer()
        client_user = self._create_client()
        visible = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        self._create_project(
            client_user,
            status=Project.Status.IN_PROGRESS,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.DRAFTED,
        )

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.get(reverse("projects:find_work"))

        project_list = list(response.context["project_list"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(project_list, [visible])

    def test_project_detail_post_creates_application_and_message(self):
        freelancer_user = self._create_freelancer()
        client_user = self._create_client()
        project = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.post(
            reverse("projects:project_detail", args=[project.id]),
            data={
                "pitch": "Hello",
                "portfolio_format": "link",
                "portfolio_url": "https://example.com",
                "availability": Application.Availability.IMMEDIATE,
            },
        )

        application = Application.objects.get(project=project, freelancer=freelancer_user)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(application.status, Application.Status.IN_REVIEW)
        self.assertTrue(
            Message.objects.filter(application=application, kind=Message.Kind.SYSTEM).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                user=client_user,
                kind=Notification.Kind.APPLY,
                conversation__project=project,
            ).exists()
        )

    def test_project_start_requires_owner(self):
        owner = self._create_client(email="owner@example.com")
        other = self._create_client(email="other@example.com")
        project = self._create_project(
            owner,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.DRAFTED,
        )

        self.client.login(username=other.email, password="Pass12345!")
        response = self.client.post(
            reverse("projects:project_start", args=[project.id])
        )

        project.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(project.status_of_publishing, Project.PublishingStatus.DRAFTED)

    def test_project_edit_requires_owner(self):
        owner = self._create_client(email="owner2@example.com")
        other = self._create_client(email="other2@example.com")
        project = self._create_project(
            owner,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )

        self.client.login(username=other.email, password="Pass12345!")
        response = self.client.get(
            reverse("projects:project_edit", args=[project.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_start_project_sets_publishing_status(self):
        owner = self._create_client(email="owner3@example.com")
        project = self._create_project(
            owner,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.DRAFTED,
        )

        self.client.login(username=owner.email, password="Pass12345!")
        response = self.client.post(
            reverse("projects:project_start", args=[project.id])
        )

        project.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(project.status_of_publishing, Project.PublishingStatus.LAUNCHED)

    def test_application_form_requires_link_when_selected(self):
        form = ApplicationForm(
            data={
                "portfolio_format": "link",
                "availability": Application.Availability.IMMEDIATE,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("portfolio_url", form.errors)

    def test_application_form_requires_file_when_selected(self):
        form = ApplicationForm(
            data={
                "portfolio_format": "file",
                "availability": Application.Availability.IMMEDIATE,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("portfolio_file", form.errors)

    def test_find_work_filters_by_tag_and_budget(self):
        freelancer_user = self._create_freelancer(email="filter@example.com")
        client_user = self._create_client(email="filterclient@example.com")
        tag = Tags.objects.create(name="Design")
        visible = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        visible.price = 400
        visible.save(update_fields=["price"])
        visible.tags.add(tag)
        hidden = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        hidden.price = 1200
        hidden.save(update_fields=["price"])

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.get(
            reverse("projects:find_work"),
            data={"tags": [tag.id], "budget": "0-500"},
        )

        project_list = list(response.context["project_list"])
        self.assertEqual(project_list, [visible])

    def test_find_work_filters_by_posted_range(self):
        freelancer_user = self._create_freelancer(email="posted@example.com")
        client_user = self._create_client(email="postedclient@example.com")
        recent = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        older = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        Project.objects.filter(id=recent.id).update(
            created_at=timezone.now() - timedelta(hours=5)
        )
        Project.objects.filter(id=older.id).update(
            created_at=timezone.now() - timedelta(days=10)
        )

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.get(
            reverse("projects:find_work"),
            data={"posted": "24h"},
        )

        project_list = list(response.context["project_list"])
        self.assertEqual(project_list, [recent])

    def test_application_completed_signal_updates_project(self):
        client_user = self._create_client(email="signalclient@example.com")
        freelancer_user = self._create_freelancer(email="signalfreelancer@example.com")
        project = self._create_project(
            client_user,
            status=Project.Status.IN_PROGRESS,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        application = Application.objects.create(
            project=project,
            freelancer=freelancer_user,
            full_name="Freelancer User",
            email="signalfreelancer@example.com",
            status=Application.Status.IN_PROGRESS,
        )

        application.status = Application.Status.COMPLETED
        application.save(update_fields=["status"])

        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.COMPLETED)

    def test_project_detail_rejects_duplicate_application(self):
        freelancer_user = self._create_freelancer(email="dupe@example.com")
        client_user = self._create_client(email="dupeclient@example.com")
        project = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        Application.objects.create(
            project=project,
            freelancer=freelancer_user,
            full_name="Dupe User",
            email="dupe@example.com",
            status=Application.Status.IN_REVIEW,
        )

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.post(
            reverse("projects:project_detail", args=[project.id]),
            data={
                "pitch": "Hello",
                "portfolio_format": "link",
                "portfolio_url": "https://example.com",
                "availability": Application.Availability.IMMEDIATE,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Application.objects.filter(project=project, freelancer=freelancer_user).count(),
            1,
        )

    def test_find_work_budget_filter_excludes_missing_price(self):
        freelancer_user = self._create_freelancer(email="price@example.com")
        client_user = self._create_client(email="priceclient@example.com")
        with_price = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        with_price.price = Decimal("450.00")
        with_price.save(update_fields=["price"])
        without_price = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        without_price.price = None
        without_price.save(update_fields=["price"])

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.get(
            reverse("projects:find_work"),
            data={"budget": "0-500"},
        )

        project_list = list(response.context["project_list"])
        self.assertEqual(project_list, [with_price])

    def test_project_attachment_clean_requires_exactly_one_source(self):
        client_user = self._create_client(email="attachclient@example.com")
        project = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        attachment = ProjectAttachment(project=project, title="Guide")

        with self.assertRaises(ValidationError):
            attachment.clean()

        attachment.url = "https://example.com"
        attachment.file = "dummy.pdf"
        with self.assertRaises(ValidationError):
            attachment.clean()

        attachment.file = None
        attachment.clean()

    def test_invitation_defaults_to_sent(self):
        client_user = self._create_client(email="invclient@example.com")
        freelancer_user = self._create_freelancer(email="invfreelancer@example.com")
        project = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        invitation = Invitation.objects.create(
            project=project,
            client=client_user,
            freelancer=freelancer_user,
            message="Join us",
        )

        self.assertEqual(invitation.status, Invitation.Status.SENT)

    def test_saved_project_unique_together(self):
        freelancer_user = self._create_freelancer(email="save@example.com")
        client_user = self._create_client(email="saveclient@example.com")
        project = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        SavedProject.objects.create(user=freelancer_user, project=project)

        with self.assertRaises(IntegrityError):
            SavedProject.objects.create(user=freelancer_user, project=project)

    def test_save_project_creates_saved_record(self):
        freelancer_user = self._create_freelancer(email="saveview@example.com")
        client_user = self._create_client(email="saveviewclient@example.com")
        project = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.post(reverse("projects:project_save", args=[project.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SavedProject.objects.filter(user=freelancer_user, project=project).exists()
        )

    def test_find_work_sorting_by_budget_high_to_low(self):
        freelancer_user = self._create_freelancer(email="sortbudget@example.com")
        client_user = self._create_client(email="sortbudgetclient@example.com")
        low = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        low.price = Decimal("100.00")
        low.save(update_fields=["price"])
        high = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        high.price = Decimal("900.00")
        high.save(update_fields=["price"])

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.get(
            reverse("projects:find_work"),
            data={"sorting": "budget_htl"},
        )

        project_list = list(response.context["project_list"])
        self.assertEqual(project_list[0], high)
        self.assertEqual(project_list[1], low)

    def test_find_work_sorting_by_deadline(self):
        freelancer_user = self._create_freelancer(email="sortdead@example.com")
        client_user = self._create_client(email="sortdeadclient@example.com")
        later = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        sooner = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        Project.objects.filter(id=sooner.id).update(
            deadline=date.today() + timedelta(days=3)
        )
        Project.objects.filter(id=later.id).update(
            deadline=date.today() + timedelta(days=10)
        )

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.get(
            reverse("projects:find_work"),
            data={"sorting": "deadline"},
        )

        project_list = list(response.context["project_list"])
        self.assertEqual(project_list[0].id, sooner.id)

    def test_find_work_filters_by_type_hourly(self):
        freelancer_user = self._create_freelancer(email="hourly@example.com")
        client_user = self._create_client(email="hourlyclient@example.com")
        hourly = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        hourly.price_type = Project.PricingType.HOURLY
        hourly.save(update_fields=["price_type"])
        fixed = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )
        fixed.price_type = Project.PricingType.FIXED
        fixed.save(update_fields=["price_type"])

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.get(
            reverse("projects:find_work"),
            data={"type": "hourly"},
        )

        project_list = list(response.context["project_list"])
        self.assertEqual(project_list, [hourly])

    def test_project_start_requires_post(self):
        owner = self._create_client(email="postowner@example.com")
        project = self._create_project(
            owner,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.DRAFTED,
        )

        self.client.login(username=owner.email, password="Pass12345!")
        response = self.client.get(reverse("projects:project_start", args=[project.id]))

        self.assertEqual(response.status_code, 405)

    def test_project_save_requires_post(self):
        freelancer_user = self._create_freelancer(email="postsave@example.com")
        client_user = self._create_client(email="postsaveclient@example.com")
        project = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )

        self.client.login(username=freelancer_user.email, password="Pass12345!")
        response = self.client.get(reverse("projects:project_save", args=[project.id]))

        self.assertEqual(response.status_code, 405)

    def test_project_update_changes_fields(self):
        owner = self._create_client(email="updateowner@example.com")
        tag = Tags.objects.create(name="Update")
        project = self._create_project(
            owner,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )

        self.client.login(username=owner.email, password="Pass12345!")
        response = self.client.post(
            reverse("projects:project_edit", args=[project.id]),
            data={
                "title": "Updated title",
                "description": "Updated description",
                "project_overview": "Updated overview",
                "responsibilities": "Updated responsibilities",
                "requirements": "Updated requirements",
                "price": "123.45",
                "price_type": Project.PricingType.FIXED,
                "deadline": (date.today() + timedelta(days=30)).isoformat(),
                "tags": [tag.id],
            },
        )

        project.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(project.title, "Updated title")

    def test_project_detail_requires_login(self):
        client_user = self._create_client(email="nologinclient@example.com")
        project = self._create_project(
            client_user,
            status=Project.Status.OPEN,
            publishing=Project.PublishingStatus.LAUNCHED,
        )

        response = self.client.get(reverse("projects:project_detail", args=[project.id]))

        self.assertEqual(response.status_code, 302)

    def test_find_work_requires_login(self):
        response = self.client.get(reverse("projects:find_work"))

        self.assertEqual(response.status_code, 302)
