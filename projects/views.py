from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from projects.models import Project, Tags


class ProjectsListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/find_work.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = Tags.objects.all()
        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
