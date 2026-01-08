from django.conf import settings
from django.contrib import messages as django_messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import signing
from django.core.mail import send_mail
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
import random

from accounts.models import Category, ClientProfile, CustomUser, FreelancerProfile
from dashboard.forms import UserProfileForm, ClientProfileForm, FreelancerProfileForm
from dashboard.models import ClientNote
from messages_app.models import Conversation, Message, Notification
from messages_app.realtime import broadcast_message, broadcast_notification
from messages_app.services import (
    create_message,
    create_notification,
    get_or_create_conversation,
)
from projects.models import Project, Milestone, Invitation
from projects.models import Application, SavedProject

EMAIL_VERIFICATION_SALT = "accounts.email-verification"
EMAIL_VERIFICATION_RESEND_SECONDS = 5 * 60
PHONE_VERIFICATION_RESEND_SECONDS = 5 * 60
PHONE_VERIFICATION_EXPIRY_SECONDS = 10 * 60


@login_required
def profile(request):
    user = request.user
    role = getattr(user, "role", "")
    role_form_class = None
    profile_obj = None

    if role == "client":
        profile_obj, _ = ClientProfile.objects.get_or_create(user=user)
        role_form_class = ClientProfileForm
    elif role == "freelancer":
        profile_obj, _ = FreelancerProfile.objects.get_or_create(
            user=user,
            defaults={
                "title": "Freelancer",
                "hourly_rate": 0,
            },
        )
        role_form_class = FreelancerProfileForm

    if request.method == "POST":
        if "profile_submit" in request.POST:
            original_email = user.email
            original_phone = user.phone_number
            user_form = UserProfileForm(request.POST, instance=user)
            role_form = (
                role_form_class(request.POST, instance=profile_obj)
                if role_form_class
                else None
            )
            password_form = PasswordChangeForm(user)
            if user_form.is_valid() and (role_form is None or role_form.is_valid()):
                updated_user = user_form.save(commit=False)
                if updated_user.email != original_email:
                    updated_user.email_verified = False
                    updated_user.email_verification_sent_at = None
                if updated_user.phone_number != original_phone:
                    updated_user.phone_verified = False
                    updated_user.phone_verification_sent_at = None
                    updated_user.phone_verification_code = ""
                updated_user.save()
                if role_form is not None:
                    role_form.save()
                django_messages.success(request, "Profile updated.")
                return redirect("dashboard:profile")
        elif "password_submit" in request.POST:
            user_form = UserProfileForm(instance=user)
            role_form = (
                role_form_class(instance=profile_obj) if role_form_class else None
            )
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                updated_user = password_form.save()
                update_session_auth_hash(request, updated_user)
                django_messages.success(request, "Password updated.")
                return redirect("dashboard:profile")
        elif "avatar_submit" in request.POST or request.FILES.get("avatar"):
            user_form = UserProfileForm(instance=user)
            role_form = (
                role_form_class(instance=profile_obj) if role_form_class else None
            )
            password_form = PasswordChangeForm(user)
            if role != "freelancer" or profile_obj is None:
                django_messages.error(request, "Avatar upload is only available for freelancers.")
            else:
                avatar_file = request.FILES.get("avatar")
                if not avatar_file:
                    django_messages.error(request, "Select an image to upload.")
                else:
                    profile_obj.avatar = avatar_file
                    profile_obj.save(update_fields=["avatar"])
                    django_messages.success(request, "Avatar updated.")
                    return redirect("dashboard:profile")
        elif "portfolio_submit" in request.POST:
            user_form = UserProfileForm(instance=user)
            role_form = (
                role_form_class(instance=profile_obj) if role_form_class else None
            )
            password_form = PasswordChangeForm(user)
            if role != "freelancer" or profile_obj is None:
                django_messages.error(request, "Portfolio updates are only available for freelancers.")
            else:
                portfolio_file = request.FILES.get("portfolio_file")
                portfolio_website = (request.POST.get("portfolio_website") or "").strip()
                if not portfolio_file and not portfolio_website:
                    django_messages.error(request, "Add a portfolio link or upload a file.")
                else:
                    update_fields = []
                    if portfolio_file:
                        profile_obj.portfolio_file = portfolio_file
                        update_fields.append("portfolio_file")
                    if portfolio_website:
                        profile_obj.portfolio_website = portfolio_website
                        update_fields.append("portfolio_website")
                    profile_obj.save(update_fields=update_fields)
                    django_messages.success(request, "Portfolio updated.")
                    return redirect("dashboard:profile")
        elif "availability_submit" in request.POST:
            user_form = UserProfileForm(instance=user)
            role_form = (
                role_form_class(instance=profile_obj) if role_form_class else None
            )
            password_form = PasswordChangeForm(user)
            if role != "freelancer" or profile_obj is None:
                django_messages.error(request, "Availability updates are only available for freelancers.")
            else:
                raw_value = (request.POST.get("weekly_capacity") or "").strip()
                try:
                    weekly_capacity = int(raw_value)
                except ValueError:
                    django_messages.error(request, "Enter a valid number of hours.")
                else:
                    if weekly_capacity < 20 or weekly_capacity > 70:
                        django_messages.error(request, "Weekly capacity must be between 20 and 70.")
                    else:
                        profile_obj.weekly_capacity = weekly_capacity
                        profile_obj.save(update_fields=["weekly_capacity"])
                        django_messages.success(request, "Availability updated.")
                        return redirect("dashboard:profile")
        else:
            user_form = UserProfileForm(instance=user)
            role_form = (
                role_form_class(instance=profile_obj) if role_form_class else None
            )
            password_form = PasswordChangeForm(user)
    else:
        user_form = UserProfileForm(instance=user)
        role_form = role_form_class(instance=profile_obj) if role_form_class else None
        password_form = PasswordChangeForm(user)

    for field_name in ["old_password", "new_password1", "new_password2"]:
        field = password_form.fields.get(field_name)
        if field:
            field.widget.attrs.update({"class": "form-control"})

    email_can_resend = True
    email_resend_minutes = 0
    email_resend_seconds = 0
    if user.email_verification_sent_at and not user.email_verified:
        elapsed = (timezone.now() - user.email_verification_sent_at).total_seconds()
        remaining = max(0, EMAIL_VERIFICATION_RESEND_SECONDS - elapsed)
        email_can_resend = remaining <= 0
        email_resend_minutes = max(1, int((remaining + 59) // 60)) if remaining else 0
        email_resend_seconds = int(remaining)

    phone_can_resend = True
    phone_resend_minutes = 0
    phone_resend_seconds = 0
    if user.phone_verification_sent_at and not user.phone_verified:
        elapsed = (timezone.now() - user.phone_verification_sent_at).total_seconds()
        remaining = max(0, PHONE_VERIFICATION_RESEND_SECONDS - elapsed)
        phone_can_resend = remaining <= 0
        phone_resend_minutes = max(1, int((remaining + 59) // 60)) if remaining else 0
        phone_resend_seconds = int(remaining)

    context = {
        "user_form": user_form,
        "role_form": role_form,
        "password_form": password_form,
        "profile_obj": profile_obj,
        "email_can_resend": email_can_resend,
        "email_resend_minutes": email_resend_minutes,
        "email_resend_seconds": email_resend_seconds,
        "phone_can_resend": phone_can_resend,
        "phone_resend_minutes": phone_resend_minutes,
        "phone_resend_seconds": phone_resend_seconds,
    }
    return render(request, "dashboard/profile.html", context)


@login_required
def overview(request):
    return redirect("dashboard:profile")


class FindTalentList(LoginRequiredMixin, ListView):
    model = FreelancerProfile
    template_name = "dashboard/freelancer/find_talent.html"
    context_object_name = "freelancers"

    def get_queryset(self):
        qs = (
            FreelancerProfile.objects.select_related("user")
            .prefetch_related("user__category")
            .filter(user__role="freelancer")
        )

        query = self.request.GET.get("q", "").strip()
        category_id = self.request.GET.get("category", "").strip()
        rate = self.request.GET.get("rate", "").strip()
        sort = self.request.GET.get("sort", "").strip()

        if query:
            qs = qs.filter(
                Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(user__email__icontains=query)
                | Q(title__icontains=query)
                | Q(bio__icontains=query)
                | Q(user__category__name__icontains=query)
            ).distinct()

        if category_id:
            qs = qs.filter(user__category__id=category_id)

        if rate == "0-25":
            qs = qs.filter(hourly_rate__lt=25)
        elif rate == "25-50":
            qs = qs.filter(hourly_rate__gte=25, hourly_rate__lte=50)
        elif rate == "50-100":
            qs = qs.filter(hourly_rate__gt=50, hourly_rate__lte=100)
        elif rate == "100+":
            qs = qs.filter(hourly_rate__gt=100)

        sort_map = {
            "rate_asc": "hourly_rate",
            "rate_desc": "-hourly_rate",
            "newest": "-joined_at",
            "oldest": "joined_at",
            "name": "user__first_name",
        }
        qs = qs.order_by(sort_map.get(sort, "-joined_at"))

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.order_by("name")
        context["selected_category"] = self.request.GET.get("category", "").strip()
        context["selected_rate"] = self.request.GET.get("rate", "").strip()
        context["selected_sort"] = self.request.GET.get("sort", "").strip()
        context["query"] = self.request.GET.get("q", "").strip()
        context["results_count"] = context["freelancers"].count()
        return context


class FindTalentDetail(LoginRequiredMixin, DetailView):
    model = FreelancerProfile
    template_name = "dashboard/freelancer/freelancer_detail.html"
    context_object_name = "freelancer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        weekly_capacity = self.object.weekly_capacity or 0
        capacity_percent = round((weekly_capacity / 70) * 100) if weekly_capacity else 0
        context["weekly_capacity"] = weekly_capacity
        context["weekly_capacity_percent"] = min(capacity_percent, 100)
        if getattr(self.request.user, "role", "") == "client":
            context["client_projects"] = Project.objects.filter(
                client__user=self.request.user
            ).order_by("-created_at")
        else:
            context["client_projects"] = []
        return context

@login_required
def messages(request):
    conversations = (
        Conversation.objects.filter(
            Q(client=request.user) | Q(freelancer=request.user)
        )
        .select_related("project", "client", "freelancer")
        .annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user),
            )
        )
        .order_by("-updated_at")
    )
    active_id = request.GET.get("conversation")
    active_conversation = None
    if active_id:
        active_conversation = conversations.filter(pk=active_id).first()
    if active_conversation is None and conversations:
        active_conversation = conversations[0]
    message_list = []
    if active_conversation:
        message_list = (
            Message.objects.filter(conversation=active_conversation)
            .select_related("sender", "application", "application__project")
            .order_by("created_at")
        )
        Message.objects.filter(
            conversation=active_conversation,
            is_read=False,
        ).exclude(sender=request.user).update(is_read=True)
        Notification.objects.filter(
            user=request.user,
            conversation=active_conversation,
            is_read=False,
        ).update(is_read=True)
    context = {
        "conversations": conversations,
        "active_conversation": active_conversation,
        "message_list": message_list,
    }
    return render(request, "messages_app/messages.html", context)


@login_required
@require_POST
def send_invite(request, freelancer_id):
    if getattr(request.user, "role", "") != "client":
        django_messages.error(request, "Only clients can send invites.")
        return redirect("dashboard:find_talent")
    project_id = request.POST.get("project_id")
    message = (request.POST.get("message") or "").strip()
    project = get_object_or_404(Project, pk=project_id, client__user=request.user)
    freelancer = get_object_or_404(CustomUser, pk=freelancer_id, role="freelancer")
    Invitation.objects.create(
        project=project,
        client=request.user,
        freelancer=freelancer,
        message=message,
        status=Invitation.Status.SENT,
    )
    conversation, _ = get_or_create_conversation(project, request.user, freelancer)
    body = message or f"Invited you to the project \"{project.title}\"."
    invite_message = create_message(
        conversation,
        request.user,
        body,
        kind=Message.Kind.SYSTEM,
    )
    invite_notification = create_notification(
        user=freelancer,
        actor=request.user,
        kind=Notification.Kind.INVITE,
        title="New project invite",
        body=f"Invite to {project.title}.",
        conversation=conversation,
    )
    broadcast_message(invite_message)
    broadcast_notification(invite_notification)
    django_messages.success(request, "Invite sent.")
    return redirect(f"{reverse('dashboard:messages')}?conversation={conversation.id}")


@login_required
@require_POST
def decide_application(request, application_id):
    action = request.POST.get("action")
    application = get_object_or_404(
        Application.objects.select_related("project", "project__client", "freelancer"),
        pk=application_id,
    )
    if application.project.client.user != request.user:
        django_messages.error(request, "You do not have access to this application.")
        return redirect("dashboard:messages")
    if action == "accept":
        application.status = Application.Status.IN_PROGRESS
        decision_label = "accepted"
        notification_kind = Notification.Kind.APPLY
        if application.project.status != Project.Status.IN_PROGRESS:
            application.project.status = Project.Status.IN_PROGRESS
            application.project.save(update_fields=["status"])
    elif action == "deny":
        application.status = Application.Status.DECLINED
        decision_label = "declined"
        notification_kind = Notification.Kind.APPLY
    elif action == "complete":
        if application.status != Application.Status.IN_PROGRESS:
            django_messages.error(request, "Only in-progress projects can be completed.")
            return redirect("dashboard:messages")
        application.status = Application.Status.COMPLETED
        decision_label = "completed"
        notification_kind = Notification.Kind.APPLY
        if application.project.status != Project.Status.COMPLETED:
            application.project.status = Project.Status.COMPLETED
            application.project.save(update_fields=["status"])
    else:
        django_messages.error(request, "Invalid action.")
        return redirect("dashboard:messages")
    application.save(update_fields=["status"])

    conversation, _ = get_or_create_conversation(
        application.project,
        application.project.client.user,
        application.freelancer,
    )
    decision_body = (
        f"Your application for \"{application.project.title}\" was {decision_label}."
    )
    decision_message = create_message(
        conversation,
        request.user,
        decision_body,
        kind=Message.Kind.SYSTEM,
        application=application,
    )
    decision_notification = create_notification(
        user=application.freelancer,
        actor=request.user,
        kind=notification_kind,
        title=f"Application {decision_label}",
        body=f"Your application for {application.project.title} was {decision_label}.",
        conversation=conversation,
    )
    broadcast_message(decision_message)
    broadcast_notification(decision_notification)
    django_messages.success(request, f"Application {decision_label}.")
    return redirect(f"{reverse('dashboard:messages')}?conversation={conversation.id}")


@login_required
def freelancer_jobs(request):
    saved_projects = SavedProject.objects.filter(user=request.user).select_related("project")
    applications = Application.objects.filter(freelancer=request.user).select_related("project")
    context = {
        "saved_projects": saved_projects,
        "applications": applications,
    }
    return render(request, "dashboard/freelancer/freelancer_jobs.html", context)


@login_required
def freelancer_portfolio(request):
    profile = None
    if getattr(request.user, "role", "") == "freelancer":
        profile, _ = FreelancerProfile.objects.get_or_create(
            user=request.user,
            defaults={
                "title": "Freelancer",
                "hourly_rate": 0,
            },
        )
    if request.method == "POST":
        if getattr(request.user, "role", "") != "freelancer" or profile is None:
            django_messages.error(request, "Portfolio updates are only available for freelancers.")
            return redirect("dashboard:freelancer_portfolio")
        portfolio_file = request.FILES.get("portfolio_file")
        if not portfolio_file:
            django_messages.error(request, "Select a portfolio file to upload.")
        else:
            profile.portfolio_file = portfolio_file
            profile.save(update_fields=["portfolio_file"])
            django_messages.success(request, "Portfolio updated.")
            return redirect("dashboard:freelancer_portfolio")
    portfolio_src = profile.portfolio_file.url if profile and profile.portfolio_file else None
    return render(
        request,
        "dashboard/freelancer/freelancer_portfolio.html",
        {"profile": profile, "portfolio_src": portfolio_src},
    )


@login_required
@require_POST
def send_email_verification(request):
    user = request.user
    if user.email_verified:
        django_messages.info(request, "Email already verified.")
        return redirect("dashboard:profile")
    if user.email_verification_sent_at:
        elapsed = (timezone.now() - user.email_verification_sent_at).total_seconds()
        if elapsed < EMAIL_VERIFICATION_RESEND_SECONDS:
            wait_seconds = int(EMAIL_VERIFICATION_RESEND_SECONDS - elapsed)
            wait_minutes = max(1, int((wait_seconds + 59) // 60))
            django_messages.warning(
                request,
                f"Please wait {wait_minutes} min before requesting a new email.",
            )
            return redirect("dashboard:profile")

    token = signing.dumps(
        {"user_id": user.pk, "email": user.email},
        salt=EMAIL_VERIFICATION_SALT,
    )
    verify_url = request.build_absolute_uri(
        reverse("dashboard:verify_email", args=[token])
    )
    message = (
        f"Hi {user.first_name or user.email},\n\n"
        "Please verify your email by clicking the link below:\n"
        f"{verify_url}\n\n"
        "If you did not request this, you can ignore this email."
    )
    send_mail(
        "Verify your email",
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=["email_verification_sent_at"])
    django_messages.success(request, "Verification email sent.")
    return redirect("dashboard:profile")


@login_required
def verify_email(request, token):
    try:
        data = signing.loads(
            token,
            salt=EMAIL_VERIFICATION_SALT,
            max_age=60 * 60 * 24,
        )
    except signing.SignatureExpired:
        django_messages.error(request, "Verification link expired. Request a new one.")
        return redirect("dashboard:profile")
    except signing.BadSignature:
        django_messages.error(request, "Invalid verification link.")
        return redirect("dashboard:profile")

    user = get_object_or_404(
        CustomUser,
        pk=data.get("user_id"),
        email=data.get("email"),
    )
    user.email_verified = True
    user.email_verification_sent_at = None
    user.save(update_fields=["email_verified", "email_verification_sent_at"])
    django_messages.success(request, "Email verified.")
    return redirect("dashboard:profile")


@login_required
@require_POST
def send_phone_verification(request):
    user = request.user
    if user.phone_verified:
        django_messages.info(request, "Phone already verified.")
        return redirect("dashboard:profile")
    if not user.phone_number:
        django_messages.error(request, "Add a phone number first.")
        return redirect("dashboard:profile")
    if user.phone_verification_sent_at:
        elapsed = (timezone.now() - user.phone_verification_sent_at).total_seconds()
        if elapsed < PHONE_VERIFICATION_RESEND_SECONDS:
            wait_seconds = int(PHONE_VERIFICATION_RESEND_SECONDS - elapsed)
            wait_minutes = max(1, int((wait_seconds + 59) // 60))
            django_messages.warning(
                request,
                f"Please wait {wait_minutes} min before requesting a new code.",
            )
            return redirect("dashboard:profile")

    code = f"{random.randint(0, 999999):06d}"
    user.phone_verification_code = code
    user.phone_verification_sent_at = timezone.now()
    user.save(update_fields=["phone_verification_code", "phone_verification_sent_at"])
    print(f"PHONE VERIFICATION CODE for {user.phone_number}: {code}")
    django_messages.success(request, "Verification code sent. Check server console.")
    return redirect("dashboard:profile")


@login_required
@require_POST
def verify_phone(request):
    user = request.user
    code = (request.POST.get("phone_code") or "").strip()
    if not user.phone_verification_sent_at or not user.phone_verification_code:
        django_messages.error(request, "Request a verification code first.")
        return redirect("dashboard:profile")

    elapsed = (timezone.now() - user.phone_verification_sent_at).total_seconds()
    if elapsed > PHONE_VERIFICATION_EXPIRY_SECONDS:
        django_messages.error(request, "Verification code expired. Request a new one.")
        return redirect("dashboard:profile")

    if code != user.phone_verification_code:
        django_messages.error(request, "Invalid verification code.")
        return redirect("dashboard:profile")

    user.phone_verified = True
    user.phone_verification_code = ""
    user.phone_verification_sent_at = None
    user.save(
        update_fields=[
            "phone_verified",
            "phone_verification_code",
            "phone_verification_sent_at",
        ]
    )
    django_messages.success(request, "Phone verified.")
    return redirect("dashboard:profile")


@login_required
def client_projects(request):
    if getattr(request.user, "role", "") == "client":
        projects_qs = (
            Project.objects.filter(client__user=request.user)
            .select_related("client")
            .prefetch_related("tags")
            .order_by("-created_at")
        )
        notes = ClientNote.objects.filter(user=request.user)
        in_progress_apps = Application.objects.filter(
            project__in=projects_qs,
            status=Application.Status.IN_PROGRESS,
        )
        in_progress_map = {app.project_id: app for app in in_progress_apps}
        projects = list(projects_qs)
        for project in projects:
            project.in_progress_application = in_progress_map.get(project.id)
    else:
        projects = []
        notes = ClientNote.objects.none()

    context = {
        "projects": projects,
        "projects_total": len(projects),
        "drafted_count": sum(
            1
            for project in projects
            if project.status_of_publishing == Project.PublishingStatus.DRAFTED
        ),
        "launched_count": sum(
            1
            for project in projects
            if project.status_of_publishing == Project.PublishingStatus.LAUNCHED
        ),
        "notes": notes,
    }
    return render(request, "dashboard/client/client_projects.html", context)


@login_required
@require_POST
def client_notes_create(request):
    if getattr(request.user, "role", "") != "client":
        return JsonResponse({"error": "Not allowed."}, status=403)

    title = request.POST.get("title", "").strip()
    body = request.POST.get("body", "").strip()
    if not title:
        return JsonResponse({"error": "Title is required."}, status=400)

    note = ClientNote.objects.create(user=request.user, title=title, body=body)
    return JsonResponse(
        {
            "id": note.id,
            "title": note.title,
            "body": note.body,
            "created_at": note.created_at.strftime("%b %d, %Y"),
        }
    )


@login_required
@require_POST
def client_notes_delete(request, note_id):
    if getattr(request.user, "role", "") != "client":
        return JsonResponse({"error": "Not allowed."}, status=403)

    note = get_object_or_404(ClientNote, id=note_id, user=request.user)
    note.delete()
    return JsonResponse({"ok": True})


@login_required
def client_hired_freelancers(request):
    status_choices = [
        choice
        for choice in Application.Status.choices
        if choice[0] != Application.Status.DECLINED
    ]
    if getattr(request.user, "role", "") != "client":
        context = {
            "hired_items": [],
            "total_applications": 0,
            "total_hired": 0,
            "active_count": 0,
            "completed_count": 0,
            "avg_rate": None,
            "results_count": 0,
            "query": "",
            "selected_status": "all",
            "selected_sort": "newest",
            "status_choices": status_choices,
            "sort_options": [
                ("newest", "Newest updates"),
                ("oldest", "Oldest updates"),
                ("rate_desc", "Highest rate"),
                ("rate_asc", "Lowest rate"),
                ("name", "Name A-Z"),
            ],
            "status_counts": {"open": 0, "in_review": 0, "in_progress": 0, "completed": 0},
            "milestones": [],
        }
        return render(request, "dashboard/client/client_hired_freelancers.html", context)

    base_qs = (
        Application.objects.filter(project__client__user=request.user)
        .exclude(status=Application.Status.DECLINED)
        .select_related("project", "freelancer", "freelancer__freelancer_profile")
        .prefetch_related("freelancer__category", "freelancer__freelancer_profile__skills")
    )

    total_applications = base_qs.count()
    total_hired = base_qs.filter(
        status__in=[Application.Status.IN_PROGRESS, Application.Status.COMPLETED]
    ).count()
    active_count = base_qs.filter(status=Application.Status.IN_PROGRESS).count()
    completed_count = base_qs.filter(status=Application.Status.COMPLETED).count()
    avg_rate = base_qs.aggregate(
        avg_rate=Avg("freelancer__freelancer_profile__hourly_rate")
    )["avg_rate"]

    status_counts = {
        "open": base_qs.filter(status=Application.Status.OPEN).count(),
        "in_review": base_qs.filter(status=Application.Status.IN_REVIEW).count(),
        "in_progress": active_count,
        "completed": completed_count,
    }

    query = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "").strip()
    selected_sort = request.GET.get("sort", "").strip()

    filtered_qs = base_qs
    if query:
        filtered_qs = filtered_qs.filter(
            Q(freelancer__first_name__icontains=query)
            | Q(freelancer__last_name__icontains=query)
            | Q(freelancer__email__icontains=query)
            | Q(project__title__icontains=query)
            | Q(freelancer__freelancer_profile__title__icontains=query)
            | Q(freelancer__freelancer_profile__bio__icontains=query)
            | Q(freelancer__freelancer_profile__skills__name__icontains=query)
            | Q(freelancer__category__name__icontains=query)
        ).distinct()

    if not selected_status:
        selected_status = "all"
    if selected_status != "all":
        filtered_qs = filtered_qs.filter(status=selected_status)

    sort_map = {
        "newest": "-created_at",
        "oldest": "created_at",
        "rate_desc": "-freelancer__freelancer_profile__hourly_rate",
        "rate_asc": "freelancer__freelancer_profile__hourly_rate",
        "name": "freelancer__first_name",
    }
    if not selected_sort:
        selected_sort = "newest"
    filtered_qs = filtered_qs.order_by(sort_map.get(selected_sort, "-created_at"))

    hired_items = []
    for app in filtered_qs:
        freelancer = app.freelancer
        try:
            profile = freelancer.freelancer_profile
        except FreelancerProfile.DoesNotExist:
            profile = None
        hired_items.append(
            {
                "application": app,
                "freelancer": freelancer,
                "profile": profile,
            }
        )

    milestones = (
        Milestone.objects.filter(project__client__user=request.user)
        .select_related("project")
        .order_by("project__title", "order")[:4]
    )

    results_count = filtered_qs.count()
    context = {
        "hired_items": hired_items,
        "total_applications": total_applications,
        "total_hired": total_hired,
        "active_count": active_count,
        "completed_count": completed_count,
        "avg_rate": avg_rate,
        "results_count": results_count,
        "query": query,
        "selected_status": selected_status,
        "selected_sort": selected_sort,
        "status_choices": status_choices,
        "sort_options": [
            ("newest", "Newest updates"),
            ("oldest", "Oldest updates"),
            ("rate_desc", "Highest rate"),
            ("rate_asc", "Lowest rate"),
            ("name", "Name A-Z"),
        ],
        "status_counts": status_counts,
        "milestones": milestones,
    }
    return render(request, "dashboard/client/client_hired_freelancers.html", context)


@login_required
def freelancer_saved_projects(request):
    return render(request, "dashboard/freelancer/freelancer_saved_projects.html")
