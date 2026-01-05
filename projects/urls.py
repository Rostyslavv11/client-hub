from django.urls import path
from projects.views import (
    ProjectsListView,
    ProjectDetailView,
    ApplicationCreateView,
    save_project,
    ProjectUpdateView,
    start_project,
    ProjectCreateView,
)

urlpatterns = [
    path("find-work/", ProjectsListView.as_view(), name="find_work"),
    path("project/create/", ProjectCreateView.as_view(), name="project_create"),
    path("project/<int:pk>", ProjectDetailView.as_view(), name="project_detail"),
    path("project/<int:pk>/edit/", ProjectUpdateView.as_view(), name="project_edit"),
    path("project/<int:pk>/start/", start_project, name="project_start"),
    path("project/<int:pk>/applyl", ApplicationCreateView.as_view(), name="project_appy"),
    path("project/<int:pk>/save/", save_project, name="project_save"),
]

app_name = "projects"
