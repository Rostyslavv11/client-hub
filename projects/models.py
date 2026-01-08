from tkinter.font import names

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import ClientProfile


class Tags(models.Model):
    name = models.CharField(max_length=100, null=False)

    def __str__(self):
        return self.name


class VibeTag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Project(models.Model):

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'

    class PublishingStatus(models.TextChoices):
        DRAFTED = "drafted", "Drafted"
        LAUNCHED = "launched", "Launched"

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

    vibe_tags = models.ManyToManyField(VibeTag, blank=True, related_name="projects")
    vibe_description = models.TextField(
        blank=True,
        default="Modern, friendly, conversion-focused vibe with clear structure and confident messaging."
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
    deadline = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    status_of_publishing = models.CharField(
        max_length=20,
        choices=PublishingStatus.choices,
        default=PublishingStatus.DRAFTED
    )
    tags = models.ManyToManyField(Tags, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    project_overview = models.TextField()
    responsibilities = models.TextField(
        help_text="What you will do (one item per line or markdown list)"
    )
    requirements = models.TextField(
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


class ProjectAttachment(models.Model):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="attachments")

    title = models.CharField(max_length=120)  # "Brand guide", "Current landing page"
    file = models.FileField(upload_to="project_attachments/%Y/%m/", blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        has_file = bool(self.file)
        has_url = bool(self.url)
        if has_file == has_url:
            raise ValidationError("Provide either a file or a URL (exactly one).")

    def __str__(self):
        return self.title


class Application(models.Model):

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_REVIEW = "in_review", "In review"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        DECLINED = "declined", "Declined"

    class Availability(models.TextChoices):
        IMMEDIATE = "immediate", "Start immediately"
        ONE_TWO_WEEKS = "1_2_wes", "1-2 weeks"
        THREE_FOUR_WEEKS = "3_4_weeks", "3-4 weeks"
        MONTH_PLUS = "month_plus", "More than a month"

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
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    pitch = models.TextField(blank=True)
    portfolio_url = models.URLField(blank=True, null=True)
    portfolio_file = models.FileField(upload_to="application_portfolios/%Y/%m/", blank=True, null=True)
    availability = models.CharField(
        max_length=20,
        choices=Availability.choices,
        default=Availability.IMMEDIATE
    )
    estimated_timeline = models.CharField(max_length=80, blank=True)
    proposed_budget = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    additional_notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        has_url = bool(self.portfolio_url)
        has_file = bool(self.portfolio_file)
        if has_url == has_file:
            raise ValidationError("Provide either a portfolio link or a portfolio file (exactly one).")


class Invitation(models.Model):
    class Status(models.TextChoices):
        SENT = "sent", "Sent"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        CANCELED = "canceled", "Canceled"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_invitations",
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_invitations",
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SENT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project.title} -> {self.freelancer_id}"


class SavedProject(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_projects"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="saved_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "project")

