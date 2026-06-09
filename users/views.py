from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChangePasswordForm, EditProfileForm, LoginForm, RegisterForm
from .models import User


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("/projects/list/")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.cleaned_data["user"])
        next_url = request.GET.get("next") or request.POST.get("next") or "/projects/list/"
        return redirect(next_url)
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/projects/list/")


def user_list_view(request):
    qs = User.objects.filter(is_active=True).order_by("id")
    active_filter = None

    if request.user.is_authenticated:
        active_filter = request.GET.get("filter")
        if active_filter == "owners-of-favorite-projects":
            fav_ids = request.user.favorites.values_list("id", flat=True)
            qs = (
                User.objects.filter(owned_projects__id__in=fav_ids)
                .distinct()
                .order_by("id")
            )
        elif active_filter == "owners-of-participating-projects":
            part_ids = request.user.participated_projects.values_list("id", flat=True)
            qs = (
                User.objects.filter(owned_projects__id__in=part_ids)
                .distinct()
                .order_by("id")
            )
        elif active_filter == "interested-in-my-projects":
            my_ids = request.user.owned_projects.values_list("id", flat=True)
            qs = (
                User.objects.filter(favorites__id__in=my_ids)
                .distinct()
                .order_by("id")
            )
        elif active_filter == "participants-of-my-projects":
            my_ids = request.user.owned_projects.values_list("id", flat=True)
            qs = (
                User.objects.filter(participated_projects__id__in=my_ids)
                .distinct()
                .order_by("id")
            )
        else:
            active_filter = None

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    query_prefix = f"filter={active_filter}&" if active_filter else ""

    return render(request, "users/participants.html", {
        "participants": qs,
        "page_obj": page_obj,
        "active_filter": active_filter,
        "query_prefix": query_prefix,
    })


def user_detail_view(request, user_id):
    user = get_object_or_404(User, id=user_id, is_active=True)
    return render(request, "users/user-details.html", {"user": user})


@login_required
def edit_profile_view(request):
    user = request.user
    form = EditProfileForm(
        request.POST or None, request.FILES or None, instance=user
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(f"/users/{user.id}/")
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password_view(request):
    form = ChangePasswordForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        login(request, request.user)
        return redirect(f"/users/{request.user.id}/")
    return render(request, "users/change_password.html", {"form": form})
