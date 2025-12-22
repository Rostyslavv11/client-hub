from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from projects.models import Project, Tags
from django.utils import timezone
from datetime import timedelta


class ProjectsListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/find_work.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by("-created_at")
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
                queryset = queryset.order_by("-deadline")

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
