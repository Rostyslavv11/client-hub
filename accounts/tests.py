from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.forms import ClientRegisterForm, FreelancerRegisterForm
from accounts.models import ClientProfile, FreelancerProfile


class AccountAuthTests(TestCase):
    def test_register_client_creates_profile_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:register_client"),
            data={
                "email": "client@example.com",
                "first_name": "Client",
                "last_name": "User",
                "password1": "Pass12345!",
                "password2": "Pass12345!",
            },
        )

        self.assertRedirects(response, reverse("home"))
        user = get_user_model().objects.get(email="client@example.com")
        self.assertEqual(user.role, "client")
        self.assertTrue(ClientProfile.objects.filter(user=user).exists())

    def test_register_freelancer_creates_profile(self):
        response = self.client.post(
            reverse("accounts:register_freelancer"),
            data={
                "email": "freelancer@example.com",
                "first_name": "Freelancer",
                "last_name": "User",
                "password1": "Pass12345!",
                "password2": "Pass12345!",
                "title": "Backend Developer",
                "hourly_rate": "40",
                "portfolio_website": "https://example.com",
            },
        )

        self.assertRedirects(response, reverse("home"))
        user = get_user_model().objects.get(email="freelancer@example.com")
        self.assertEqual(user.role, "freelancer")
        self.assertTrue(FreelancerProfile.objects.filter(user=user).exists())

    def test_login_view_redirects_home_on_success(self):
        user = get_user_model().objects.create_user(
            email="login@example.com",
            password="Pass12345!",
            first_name="Login",
            last_name="User",
        )
        response = self.client.post(
            reverse("accounts:login"),
            data={"username": user.email, "password": "Pass12345!"},
        )

        self.assertRedirects(response, reverse("home"))

    def test_login_view_redirects_to_next(self):
        user = get_user_model().objects.create_user(
            email="next@example.com",
            password="Pass12345!",
            first_name="Next",
            last_name="User",
        )
        response = self.client.post(
            reverse("accounts:login"),
            data={
                "username": user.email,
                "password": "Pass12345!",
                "next": reverse("projects:find_work"),
            },
        )

        self.assertRedirects(response, reverse("projects:find_work"))

    def test_logout_redirects_home(self):
        user = get_user_model().objects.create_user(
            email="logout@example.com",
            password="Pass12345!",
            first_name="Log",
            last_name="Out",
        )
        self.client.login(username=user.email, password="Pass12345!")
        response = self.client.get(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("home"))


class AccountFormValidationTests(TestCase):
    def test_client_register_invalid_location(self):
        form = ClientRegisterForm(
            data={
                "email": "badloc@example.com",
                "first_name": "Bad",
                "last_name": "Location",
                "password1": "Pass12345!",
                "password2": "Pass12345!",
                "location": "Kyiv Ukraine",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("location", form.errors)

    def test_freelancer_register_requires_portfolio(self):
        form = FreelancerRegisterForm(
            data={
                "email": "nopor@example.com",
                "first_name": "No",
                "last_name": "Portfolio",
                "password1": "Pass12345!",
                "password2": "Pass12345!",
                "title": "Developer",
                "hourly_rate": "50",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("portfolio_website", form.errors)
        self.assertIn("portfolio_file", form.errors)

    def test_freelancer_register_rejects_link_and_file(self):
        upload = SimpleUploadedFile("portfolio.txt", b"test file")
        form = FreelancerRegisterForm(
            data={
                "email": "both@example.com",
                "first_name": "Both",
                "last_name": "Portfolio",
                "password1": "Pass12345!",
                "password2": "Pass12345!",
                "title": "Developer",
                "hourly_rate": "50",
                "portfolio_website": "https://example.com",
            },
            files={"portfolio_file": upload},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("portfolio_website", form.errors)
        self.assertIn("portfolio_file", form.errors)


class AccountModelTests(TestCase):
    def test_client_profile_rating_rounding(self):
        user = get_user_model().objects.create_user(
            email="rating@example.com",
            password="Pass12345!",
            first_name="Rate",
            last_name="User",
        )
        profile = ClientProfile.objects.create(
            user=user,
            company_name="Acme",
            hire_rate=33,
        )

        self.assertEqual(profile.rating_5, Decimal("1.65"))
