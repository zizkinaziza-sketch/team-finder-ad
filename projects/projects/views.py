from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm
from .models import Project


def project_list_view(request):
    projects = Project.objects.select_related("owner").order_by("-created_at")
    paginator = Paginator(projects, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
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
        return redirect(f"/projects/{project.id}/")
    return render(request, "projects/create-project.html", {"form": form, "is_edit": False})


@login_required
def edit_project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(f"/projects/{project.id}/")
    return render(request, "projects/create-project.html", {"form": form, "is_edit": True})


@login_required
def complete_project_view(request, project_id):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=405)
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    if project.status != "open":
        return JsonResponse({"status": "error", "message": "Already closed"}, status=400)
    project.status = "closed"
    project.save()
    return JsonResponse({"status": "ok", "project_status": "closed"})


@login_required
def toggle_participate_view(request, project_id):
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=405)
    project = get_object_or_404(Project, id=project_id)
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
        return JsonResponse({"status": "error"}, status=405)
    project = get_object_or_404(Project, id=project_id)
    user = request.user
    if user.favorites.filter(id=project.id).exists():
        user.favorites.remove(project)
        return JsonResponse({"status": "ok", "favorited": False})
    user.favorites.add(project)
    return JsonResponse({"status": "ok", "favorited": True})
