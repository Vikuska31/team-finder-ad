from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from projects.constants import PROJECTS_PER_PAGE
from projects.forms import ProjectForm
from projects.models import Project


def project_list(request):
    projects = Project.objects.select_related("owner")
    paginator = Paginator(projects, PROJECTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "projects/project_list.html",
        {"projects": projects, "page_obj": page_obj},
    )


def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
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
    project = get_object_or_404(Project, id=project_id)
    if project.owner != request.user or project.status != Project.Status.OPEN:
        return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)
    project.status = Project.Status.CLOSED
    project.save()
    return JsonResponse({"status": "ok", "project_status": project.status})


@login_required
@require_POST
def toggle_participate(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    participant = request.user not in project.participants.all()
    if participant:
        project.participants.add(request.user)
    else:
        project.participants.remove(request.user)
    return JsonResponse({"status": "ok", "participant": participant})


@login_required
@require_POST
def toggle_favorite(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    favorited = project not in request.user.favorites.all()
    if favorited:
        request.user.favorites.add(project)
    else:
        request.user.favorites.remove(project)
    return JsonResponse({"status": "ok", "favorited": favorited})


@login_required
def favorites(request):
    projects = request.user.favorites.select_related("owner")
    return render(
        request,
        "projects/favorite_projects.html",
        {"projects": projects},
    )
