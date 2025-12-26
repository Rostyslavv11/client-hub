from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from projects.models import Application, SavedProject


@login_required
def overview(request):
    return render(request, "dashboard/overview.html")


@login_required
def find_talent(request):
    freelancers = [
        {"name": "Alina Petrenko", "role": "UI/UX Designer", "rate": "$45/hr", "category": "Design", "applied": "2 days ago", "skills": ["Figma", "Webflow", "Design systems"]},
        {"name": "Dmytro Kovalenko", "role": "Full-stack Developer", "rate": "$60/hr", "category": "Development", "applied": "5 hours ago", "skills": ["Django", "React", "REST"]},
        {"name": "Iryna Sydor", "role": "Content Strategist", "rate": "$35/hr", "category": "Content", "applied": "1 day ago", "skills": ["Copywriting", "SEO", "Email"]},
    ]
    return render(request, "dashboard/find_talent.html", {"freelancers": freelancers})


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
    return render(request, "dashboard/freelancer_jobs.html", context)


@login_required
def freelancer_earnings(request):
    return render(request, "dashboard/freelancer_earnings.html")


@login_required
def freelancer_portfolio(request):
    profile = getattr(request.user, "freelancer_profile", None)
    return render(request, "dashboard/freelancer_portfolio.html", {"profile": profile})


@login_required
def client_projects(request):
    return render(request, "dashboard/client_projects.html")


@login_required
def client_hired_freelancers(request):
    return render(request, "dashboard/client_hired_freelancers.html")


@login_required
def client_payments(request):
    return render(request, "dashboard/client_payments.html")


@login_required
def freelancer_saved_projects(request):
    return render(request, "dashboard/freelancer_saved_projects.html")
