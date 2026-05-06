"""Reusable permission helpers for HTML views (DRF permissions live in api/)."""

from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden


def is_admin(user) -> bool:
    return user.is_authenticated and (
        getattr(user, "is_admin", False) or user.is_superuser
    )


def is_project_member(user, project) -> bool:
    if not user.is_authenticated:
        return False
    if is_admin(user):
        return True
    if project.owner_id == user.id:
        return True
    return project.memberships.filter(user=user).exists()


def can_edit_task(user, task) -> bool:
    if not user.is_authenticated:
        return False
    if is_admin(user):
        return True
    if task.created_by_id == user.id or task.assignee_id == user.id:
        return True
    return is_project_member(user, task.project)


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, "Admins only — you don't have permission for that.")
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


def project_member_required(view_func):
    """Use as a decorator on views that take a `pk` for the project."""

    @wraps(view_func)
    def _wrapped(request, pk, *args, **kwargs):
        from .models import Project
        project = Project.objects.filter(pk=pk).first()
        if not project:
            return HttpResponseForbidden("Project not found.")
        if not is_project_member(request.user, project):
            messages.error(request, "You're not a member of this project.")
            raise PermissionDenied
        return view_func(request, pk, *args, **kwargs)
    return _wrapped
