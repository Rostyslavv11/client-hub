from django.contrib import messages as django_messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from urllib.parse import urlsplit

from accounts.models import Category, ClientProfile, FreelancerProfile
from dashboard.forms import UserProfileForm, ClientProfileForm, FreelancerProfileForm
from dashboard.models import ClientNote
from projects.models import Project, Milestone
from projects.models import Application, SavedProject


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
            user_form = UserProfileForm(request.POST, instance=user)
            role_form = (
                role_form_class(request.POST, instance=profile_obj)
                if role_form_class
                else None
            )
            password_form = PasswordChangeForm(user)
            if user_form.is_valid() and (role_form is None or role_form.is_valid()):
                updated_user = user_form.save(commit=False)
                if updated_user.email != user.email:
                    updated_user.email_verified = False
                if updated_user.phone_number != user.phone_number:
                    updated_user.phone_verified = False
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

    context = {
        "user_form": user_form,
        "role_form": role_form,
        "password_form": password_form,
        "profile_obj": profile_obj,
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
    return render(request, "dashboard/messages.html")


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
def freelancer_earnings(request):
    return render(request, "dashboard/freelancer/freelancer_earnings.html")


@login_required
def freelancer_portfolio(request):
    profile = getattr(request.user, "freelancer_profile", None)
    portfolio_src = profile.portfolio_file.url if profile and profile.portfolio_file else None
    return render(
        request,
        "dashboard/freelancer/freelancer_portfolio.html",
        {"profile": profile, "portfolio_src": portfolio_src},
    )


@login_required
def client_projects(request):
    if getattr(request.user, "role", "") == "client":
        projects = (
            Project.objects.filter(client__user=request.user)
            .select_related("client")
            .prefetch_related("tags")
            .order_by("-created_at")
        )
        notes = ClientNote.objects.filter(user=request.user)
    else:
        projects = Project.objects.none()
        notes = ClientNote.objects.none()

    context = {
        "projects": projects,
        "projects_total": projects.count(),
        "drafted_count": projects.filter(
            status_of_publishing=Project.PublishingStatus.DRAFTED
        ).count(),
        "launched_count": projects.filter(
            status_of_publishing=Project.PublishingStatus.LAUNCHED
        ).count(),
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
            "status_choices": Application.Status.choices,
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
        "status_choices": Application.Status.choices,
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
def client_payments(request):
    return render(request, "dashboard/client/client_payments.html")


@login_required
def freelancer_saved_projects(request):
    return render(request, "dashboard/freelancer/freelancer_saved_projects.html")
