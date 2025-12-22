from django.conf import settings
from django.db import models

from accounts.models import ClientProfile


class Tags(models.Model):
    name = models.CharField(max_length=100, null=False)

    def __str__(self):
        return self.name


class Project(models.Model):

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'

    class PricingType(models.TextChoices):
        HOURLY = "hourly", "Hourly"
        FIXED = "fixed", "Fixed-price"

    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="projects"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_projects"
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    price_type = models.CharField(
        max_length=20,
        choices=PricingType.choices,
        default=PricingType.FIXED
    )
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    tags = models.ManyToManyField(Tags, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    project_overview = models.TextField(blank=True)
    responsibilities = models.TextField(
        blank=True,
        help_text="What you will do (one item per line or markdown list)"
    )
    requirements = models.TextField(
        blank=True,
        help_text="Requirements of client (one item per line or markdown list)"
    )


    def __str__(self):
        return self.title


class Milestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=120)
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]


class Application(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="freelancers"
    )
    proposed_budget = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    cover_letter = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
