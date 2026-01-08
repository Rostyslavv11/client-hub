from django.urls import path
from dashboard import views
from dashboard.views import FindTalentList, FindTalentDetail


app_name = "dashboard"

urlpatterns = [
    path("overview/", views.overview, name="overview"),
    path("profile/", views.profile, name="profile"),
    path("find-talent/", FindTalentList.as_view(), name="find_talent"),
    path("find-talent/<int:pk>/", FindTalentDetail.as_view(), name="freelancer_detail"),
    path("find-talent/<int:freelancer_id>/invite/", views.send_invite, name="send_invite"),
    path("applications/<int:application_id>/decision/", views.decide_application, name="decide_application"),
    path("messages/", views.messages, name="messages"),
    path("freelancer/jobs/", views.freelancer_jobs, name="freelancer_jobs"),
    path("freelancer/portfolio/", views.freelancer_portfolio, name="freelancer_portfolio"),
    path("profile/verify-email/", views.send_email_verification, name="send_email_verification"),
    path("profile/verify-email/<str:token>/", views.verify_email, name="verify_email"),
    path("profile/verify-phone/", views.send_phone_verification, name="send_phone_verification"),
    path("profile/verify-phone/confirm/", views.verify_phone, name="verify_phone"),
    path("client/projects/", views.client_projects, name="client_projects"),
    path("client/notes/create/", views.client_notes_create, name="client_notes_create"),
    path("client/notes/<int:note_id>/delete/", views.client_notes_delete, name="client_notes_delete"),
    path("client/hired-freelancers/", views.client_hired_freelancers, name="client_hired_freelancers"),
    path("freelancer/saved-projects/", views.freelancer_saved_projects, name="freelancer_saved_projects"),
]
