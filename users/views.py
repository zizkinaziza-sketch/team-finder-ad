from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from team_finder.utils import paginate

from .forms import ChangePasswordForm, EditProfileForm, LoginForm, RegisterForm
from .models import User

FILTER_OWNERS_OF_FAVORITE_PROJECTS = "owners-of-favorite-projects"
FILTER_OWNERS_OF_PARTICIPATING_PROJECTS = "owners-of-participating-projects"
FILTER_INTERESTED_IN_MY_PROJECTS = "interested-in-my-projects"
FILTER_PARTICIPANTS_OF_MY_PROJECTS = "participants-of-my-projects"


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("projects:list")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.cleaned_data["user"])
        next_url = (
            request.GET.get("next")
            or request.POST.get("next")
            or reverse("projects:list")
        )
        return redirect(next_url)
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def user_list_view(request):
    qs = User.objects.filter(is_active=True)
    active_filter = None

    if request.user.is_authenticated:
        active_filter = request.GET.get("filter")
        if active_filter == FILTER_OWNERS_OF_FAVORITE_PROJECTS:
            qs = User.objects.filter(
                owned_projects__in=request.user.favorites.all()
            ).distinct()
        elif active_filter == FILTER_OWNERS_OF_PARTICIPATING_PROJECTS:
            qs = User.objects.filter(
                owned_projects__in=request.user.participated_projects.all()
            ).distinct()
        elif active_filter == FILTER_INTERESTED_IN_MY_PROJECTS:
            qs = User.objects.filter(
                favorites__in=request.user.owned_projects.all()
            ).distinct()
        elif active_filter == FILTER_PARTICIPANTS_OF_MY_PROJECTS:
            qs = User.objects.filter(
                participated_projects__in=request.user.owned_projects.all()
            ).distinct()
        else:
            active_filter = None

    qs = qs.prefetch_related("owned_projects", "participated_projects").order_by("id")
    page_obj = paginate(qs, request.GET.get("page"))
    query_prefix = f"filter={active_filter}&" if active_filter else ""

    return render(request, "users/participants.html", {
        "participants": qs,
        "page_obj": page_obj,
        "active_filter": active_filter,
        "query_prefix": query_prefix,
    })


def user_detail_view(request, user_id):
    user = get_object_or_404(
        User.objects.prefetch_related("owned_projects__participants"),
        id=user_id,
        is_active=True,
    )
    return render(request, "users/user-details.html", {"user": user})


@login_required
def edit_profile_view(request):
    user = request.user
    form = EditProfileForm(
        request.POST or None, request.FILES or None, instance=user
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:detail", user_id=user.id)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password_view(request):
    form = ChangePasswordForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        login(request, request.user)
        return redirect("users:detail", user_id=request.user.id)
    return render(request, "users/change_password.html", {"form": form})
