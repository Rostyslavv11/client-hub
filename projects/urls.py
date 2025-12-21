from django.urls import path
from projects.views import ProjectsListView, ProjectDetailView


urlpatterns = [
    path("find-work/", ProjectsListView.as_view(), name="find_work"),
    path("project/<int:pk>", ProjectDetailView.as_view(), name="project_detail")
]

app_name = "projects"