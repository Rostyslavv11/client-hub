from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("User should have email")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("superuser should have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("superuser should have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class Category(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):

    ROLE_CHOICES = (
        ("freelancer", "Freelancer"),
        ("client", "Client"),
    )

    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="client"
    )
    category = models.ManyToManyField(
        Category,
        blank=True,
        related_name="custom_users"
    )
    phone_number = models.CharField(max_length=30, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    phone_verification_sent_at = models.DateTimeField(null=True, blank=True)
    phone_verification_code = models.CharField(max_length=6, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class ClientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_profile"
    )
    company_name = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    is_open_to_agencies = models.BooleanField(default=False)
    hire_rate = models.PositiveIntegerField(default=0)

    @property
    def rating_5(self):
        rate = Decimal(self.hire_rate or 0)
        rating = (rate * Decimal("5")) / Decimal("100")
        return rating.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class FreelancerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="freelancer_profile"
    )
    title = models.CharField(max_length=255)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)
    bio = models.TextField(blank=True)
    portfolio_website = models.URLField(blank=True)
    location = models.CharField(max_length=255, default="Not provided")
    weekly_capacity = models.PositiveSmallIntegerField(
        default=40,
        validators=[MinValueValidator(20), MaxValueValidator(70)]
    )
    portfolio_file = models.FileField(
        upload_to="freelancer_portfolios/%Y/%m/",
        blank=True,
        null=True
    )
    skills = models.ManyToManyField(Skill, blank=True, related_name="freelancers")
    avatar = models.ImageField(blank=True, upload_to="avatars/")
    joined_at = models.DateTimeField(auto_now_add=True)
