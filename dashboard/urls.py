from django.urls import path
from dashboard import views


app_name = "dashboard"

urlpatterns = [
    path("overview/", views.overview, name="overview"),
    path("find-talent/", views.find_talent, name="find_talent"),
    path("messages/", views.messages, name="messages"),
    path("freelancer/jobs/", views.freelancer_jobs, name="freelancer_jobs"),
    path("freelancer/earnings/", views.freelancer_earnings, name="freelancer_earnings"),
    path("freelancer/portfolio/", views.freelancer_portfolio, name="freelancer_portfolio"),
    path("client/projects/", views.client_projects, name="client_projects"),
    path("client/hired-freelancers/", views.client_hired_freelancers, name="client_hired_freelancers"),
    path("client/payments/", views.client_payments, name="client_payments"),
    path("freelancer/saved-projects/", views.freelancer_saved_projects, name="freelancer_saved_projects"),
]
