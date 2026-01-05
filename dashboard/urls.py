from django.urls import path
from dashboard import views
from dashboard.views import FindTalentList, FindTalentDetail


app_name = "dashboard"

urlpatterns = [
    path("overview/", views.overview, name="overview"),
    path("profile/", views.profile, name="profile"),
    path("find-talent/", FindTalentList.as_view(), name="find_talent"),
    path("find-talent/<int:pk>/", FindTalentDetail.as_view(), name="freelancer_detail"),
    path("messages/", views.messages, name="messages"),
    path("freelancer/jobs/", views.freelancer_jobs, name="freelancer_jobs"),
    path("freelancer/earnings/", views.freelancer_earnings, name="freelancer_earnings"),
    path("freelancer/portfolio/", views.freelancer_portfolio, name="freelancer_portfolio"),
    path("client/projects/", views.client_projects, name="client_projects"),
    path("client/notes/create/", views.client_notes_create, name="client_notes_create"),
    path("client/notes/<int:note_id>/delete/", views.client_notes_delete, name="client_notes_delete"),
    path("client/hired-freelancers/", views.client_hired_freelancers, name="client_hired_freelancers"),
    path("client/payments/", views.client_payments, name="client_payments"),
    path("freelancer/saved-projects/", views.freelancer_saved_projects, name="freelancer_saved_projects"),
]
