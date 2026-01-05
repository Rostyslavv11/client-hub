from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Count, Q
from django.urls import reverse
from urllib.parse import urlencode

from .forms import ClientRegisterForm, FreelancerRegisterForm, LoginForm
from .models import Category, CustomUser
from projects.models import Project


def index(request):
    categories = (
        Category.objects.annotate(
            freelancer_count=Count(
                "custom_users",
                filter=Q(custom_users__role="freelancer"),
                distinct=True,
            )
        )
        .order_by("name")
    )
    return render(request, "index.html", {"categories": categories})


def about(request):
    active_clients = CustomUser.objects.filter(
        role="client", client_profile__isnull=False
    ).count()
    freelancers_onboarded = CustomUser.objects.filter(role="freelancer").count()
    projects_launched = Project.objects.filter(
        status_of_publishing=Project.PublishingStatus.LAUNCHED
    ).count()
    context = {
        "active_clients": active_clients,
        "freelancers_onboarded": freelancers_onboarded,
        "projects_launched": projects_launched,
    }
    return render(request, "about.html", context)


def register_choice(request):
    return render(request, "accounts/register_choice.html")


def register_client(request):
    if request.method == "POST":
        form = ClientRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = ClientRegisterForm()

    return render(request, "accounts/register_client.html", {"form": form})


def register_freelancer(request):
    if request.method == "POST":
        form = FreelancerRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = FreelancerRegisterForm()

    return render(request, "accounts/register_freelancer.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            redirect_to = request.POST.get("next") or request.GET.get("next")
            if redirect_to and url_has_allowed_host_and_scheme(
                redirect_to,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(redirect_to)
            return redirect("home")

        categories = (
            Category.objects.annotate(
                freelancer_count=Count(
                    "custom_users",
                    filter=Q(custom_users__role="freelancer"),
                    distinct=True,
                )
            )
            .order_by("name")
        )
        return render(
            request,
            "index.html",
            {
                "categories": categories,
                "login_form": form,
                "show_login_modal": True,
                "login_next": request.POST.get("next") or "",
            },
        )

    if request.user.is_authenticated:
        return redirect("home")

    redirect_to = request.GET.get("next")
    query = {"login": "1"}
    if redirect_to and url_has_allowed_host_and_scheme(
        redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        query["next"] = redirect_to

    return redirect(f"{reverse('home')}?{urlencode(query)}")


def logout_view(request):
    logout(request)
    return redirect("home")




