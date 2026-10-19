from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from projects.constants import PROJECTS_PER_PAGE
from projects.forms import ProjectForm
from projects.models import Project
from team_finder.utils import get_page


def not_found():
    """Ответ в JSON для эндпоинтов, когда проекта нет в базе."""
    return JsonResponse(
        {"status": "error", "error": "Проект не найден"},
        status=HTTPStatus.NOT_FOUND,
    )


def project_list(request):
    projects = Project.objects.select_related("owner").prefetch_related(
        "participants"
    )
    return render(
        request,
        "projects/project_list.html",
        {
            "projects": projects,
            "page_obj": get_page(request, projects, PROJECTS_PER_PAGE),
        },
    )


def project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related(
            "participants"
        ),
        id=project_id,
    )
    return render(
        request,
        "projects/project-details.html",
        {"project": project},
    )


@login_required
def project_form(request, project_id=None):
    project = None
    if project_id is not None:
        project = get_object_or_404(Project, id=project_id)
        if project.owner != request.user:
            raise PermissionDenied
    form = ProjectForm(request.POST or None, instance=project)
    if not form.is_valid():
        return render(
            request,
            "projects/create-project.html",
            {"form": form, "is_edit": project is not None},
        )
    project = form.save(commit=False)
    project.owner = request.user
    project.save()
    project.participants.add(request.user)
    return redirect("projects:detail", project_id=project.id)


@login_required
@require_POST
def complete(request, project_id):
    project = Project.objects.filter(id=project_id).first()
    if project is None:
        return not_found()
    if project.owner != request.user or project.status != Project.Status.OPEN:
        return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)
    project.status = Project.Status.CLOSED
    project.save()
    return JsonResponse({"status": "ok", "project_status": project.status})


@login_required
@require_POST
def toggle_participate(request, project_id):
    project = Project.objects.filter(id=project_id).first()
    if project is None:
        return not_found()
    participant = not project.participants.filter(pk=request.user.pk).exists()
    if participant:
        project.participants.add(request.user)
    else:
        project.participants.remove(request.user)
    return JsonResponse({"status": "ok", "participant": participant})


@login_required
@require_POST
def toggle_favorite(request, project_id):
    project = Project.objects.filter(id=project_id).first()
    if project is None:
        return not_found()
    favorited = not request.user.favorites.filter(pk=project.pk).exists()
    if favorited:
        request.user.favorites.add(project)
    else:
        request.user.favorites.remove(project)
    return JsonResponse({"status": "ok", "favorited": favorited})


@login_required
def favorites(request):
    projects = request.user.favorites.select_related("owner").prefetch_related(
        "participants"
    )
    return render(
        request,
        "projects/favorite_projects.html",
        {"projects": projects},
    )
