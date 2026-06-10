from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from team_finder.utils import paginate

from .forms import ProjectForm
from .models import STATUS_CLOSED, STATUS_OPEN, Project


def project_list_view(request):
    projects = Project.objects.select_related("owner").order_by("-created_at")
    page_obj = paginate(projects, request.GET.get("page"))
    return render(request, "projects/project_list.html", {
        "projects": projects,
        "page_obj": page_obj,
        "query_prefix": "",
    })


def project_detail_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_project_view(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        return redirect("projects:detail", project_id=project.id)
    return render(request, "projects/create-project.html", {"form": form, "is_edit": False})


@login_required
def edit_project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("projects:detail", project_id=project.id)
    return render(request, "projects/create-project.html", {"form": form, "is_edit": True})


@login_required
def complete_project_view(request, project_id):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=HTTPStatus.METHOD_NOT_ALLOWED)
    project = Project.objects.filter(id=project_id, owner=request.user).first()
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Project not found"},
            status=HTTPStatus.NOT_FOUND,
        )
    if project.status != STATUS_OPEN:
        return JsonResponse(
            {"status": "error", "message": "Already closed"},
            status=HTTPStatus.BAD_REQUEST,
        )
    project.status = STATUS_CLOSED
    project.save()
    return JsonResponse({"status": "ok", "project_status": STATUS_CLOSED})


@login_required
def toggle_participate_view(request, project_id):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=HTTPStatus.METHOD_NOT_ALLOWED)
    project = Project.objects.filter(id=project_id).first()
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Project not found"},
            status=HTTPStatus.NOT_FOUND,
        )
    user = request.user
    if project.participants.filter(id=user.id).exists():
        project.participants.remove(user)
        return JsonResponse({"status": "ok", "participant": False})
    project.participants.add(user)
    return JsonResponse({"status": "ok", "participant": True})


@login_required
def favorites_view(request):
    projects = request.user.favorites.order_by("-created_at")
    return render(request, "projects/favorite_projects.html", {"projects": projects})


@login_required
def toggle_favorite_view(request, project_id):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=HTTPStatus.METHOD_NOT_ALLOWED)
    project = Project.objects.filter(id=project_id).first()
    if project is None:
        return JsonResponse(
            {"status": "error", "message": "Project not found"},
            status=HTTPStatus.NOT_FOUND,
        )
    user = request.user
    if user.favorites.filter(id=project.id).exists():
        user.favorites.remove(project)
        return JsonResponse({"status": "ok", "favorited": False})
    user.favorites.add(project)
    return JsonResponse({"status": "ok", "favorited": True})
