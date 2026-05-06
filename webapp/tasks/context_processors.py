"""Inject lightweight counters into every template (sidebar badges)."""

from django.db.models import Q


def sidebar_counts(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"sidebar_project_count": 0, "sidebar_open_task_count": 0}
    try:
        from .models import Project, Task
        if getattr(user, "is_admin", False) or user.is_superuser:
            project_count = Project.objects.count()
            open_task_count = Task.objects.exclude(status=Task.Status.DONE).count()
        else:
            project_count = Project.objects.filter(
                Q(owner=user) | Q(members=user)
            ).distinct().count()
            open_task_count = Task.objects.filter(
                assignee=user
            ).exclude(status=Task.Status.DONE).count()
    except Exception:
        # Migrations not applied yet, etc.
        project_count = open_task_count = 0
    return {
        "sidebar_project_count": project_count,
        "sidebar_open_task_count": open_task_count,
    }
