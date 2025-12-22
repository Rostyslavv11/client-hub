from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
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


class FreelancerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="freelancer_profile"
    )
    bio = models.TextField(blank=True)
    portfolio_website = models.URLField(blank=True)
    avatar = models.ImageField(blank=True, upload_to="avatars/")
