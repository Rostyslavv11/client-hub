from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse

from projects.forms import ApplicationForm, ProjectForm
from projects.models import Project, Tags, Application, SavedProject
from django.utils import timezone
from datetime import timedelta


class ProjectsListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/find_work.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            status_of_publishing=Project.PublishingStatus.LAUNCHED
        ).order_by("-created_at")
        sorting = self.request.GET.get("sorting")
        q = self.request.GET.get("q")
        tag_ids = self.request.GET.getlist("tags")
        project_type = self.request.GET.get("type")
        budget = self.request.GET.get("budget")
        posted = self.request.GET.get("posted")

        if q:
            q = q.strip()
            if q:
                queryset = queryset.filter(
                    Q(title__icontains=q) |
                    Q(description__icontains=q)
                ).distinct()

        if sorting:
            if sorting == "budget_htl":
                queryset = queryset.order_by("-price")
            if sorting == "budget_lth":
                queryset = queryset.order_by("price")
            if sorting == "deadline":
                queryset = queryset.order_by("deadline")

        if project_type == "hourly":
            budget = ""
            queryset = queryset.filter(price_type="hourly")

        if budget:
            if budget == "0-500":
                queryset = queryset.filter(price__lte=500)
            elif budget == "501-2000":
                queryset = queryset.filter(price__gt=500, price__lte=2000)
            elif budget == "2000+":
                queryset = queryset.filter(price__gt=2000)

        if tag_ids:
            queryset = queryset.filter(tags__id__in=tag_ids).distinct()

        if posted:
            now = timezone.now()
            if posted == "24h":
                queryset = queryset.filter(created_at__gte=now - timedelta(hours=24))
            if posted == "7d":
                queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
            if posted == "30d":
                queryset = queryset.filter(created_at__gte=now - timedelta(days=30))

        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = Tags.objects.all()
        context["selected_tags"] = set(map(int, self.request.GET.getlist("tags")))
        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ApplicationForm()
        context["has_applied"] = Application.objects.filter(
            project=self.object,
            freelancer=self.request.user
        ).exists()
        context["is_saved"] = SavedProject.objects.filter(
            user=self.request.user,
            project=self.object
        ).exists()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if Application.objects.filter(project=self.object, freelancer=request.user).exists():
            messages.info(request, "You’ve already applied for this project")
            return redirect("projects:project_detail", pk=self.object.pk)
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.freelancer = request.user
            form.instance.project = self.object
            form.instance.status = Application.Status.IN_REVIEW
            form.save()
            messages.success(request, "Application submitted successfully")
            return redirect("projects:project_detail", pk=self.object.pk)
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)


@login_required
@require_POST
def save_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    SavedProject.objects.get_or_create(user=request.user, project=project)
    messages.success(request, "Project saved")
    return redirect("projects:project_detail", pk=pk)


class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = "projects/project_detail.html"

    def form_valid(self, form):
        form.instance.freelancer = self.request.user
        form.instance.project_id = self.kwargs["project_id"]
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "dashboard/client/project_edit.html"

    def get_queryset(self):
        return Project.objects.filter(client__user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Project updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:client_projects")


@login_required
@require_POST
def start_project(request, pk):
    project = get_object_or_404(Project, pk=pk, client__user=request.user)
    project.status_of_publishing = Project.PublishingStatus.LAUNCHED
    project.save(update_fields=["status_of_publishing"])
    messages.success(request, "Project launched and visible in Find Work.")
    return redirect("dashboard:client_projects")


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "dashboard/client/project_create.html"

    def dispatch(self, request, *args, **kwargs):
        if getattr(request.user, "role", "") != "client":
            messages.error(request, "Only clients can create projects.")
            return redirect("dashboard:client_projects")
        if not hasattr(request.user, "client_profile"):
            messages.error(request, "Client profile is missing.")
            return redirect("dashboard:client_projects")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.client = self.request.user.client_profile
        form.instance.created_by = self.request.user
        form.instance.status_of_publishing = Project.PublishingStatus.DRAFTED
        messages.success(self.request, "Project created as drafted.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("dashboard:client_projects")
