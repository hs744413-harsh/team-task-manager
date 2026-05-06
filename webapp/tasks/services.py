"""Small helpers used by views and the API to keep both layers consistent."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from .models import Activity, Project, Task

User = get_user_model()


def visible_projects_for(user):
    """Return the projects the given user is allowed to see."""
    if not user.is_authenticated:
        return Project.objects.none()
    if getattr(user, "is_admin", False) or user.is_superuser:
        return Project.objects.all()
    return Project.objects.filter(Q(owner=user) | Q(members=user)).distinct()


def visible_tasks_for(user):
    """Return tasks within projects the user can see."""
    if not user.is_authenticated:
        return Task.objects.none()
    project_ids = visible_projects_for(user).values_list("pk", flat=True)
    return Task.objects.filter(project_id__in=project_ids)


def log_activity(actor, verb, *, project=None, task=None, description=""):
    if not actor or not actor.is_authenticated:
        return None
    return Activity.objects.create(
        actor=actor, verb=verb, project=project, task=task,
        description=description[:255] or verb,
    )


def dashboard_context(user):
    """Build the data structure used by both the HTML dashboard and the
    `api/dashboard/stats/` endpoint."""
    projects = visible_projects_for(user)
    tasks = visible_tasks_for(user)

    today = timezone.now().date()
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status=Task.Status.DONE).count()
    pending_tasks = tasks.exclude(status=Task.Status.DONE).count()
    overdue_tasks = tasks.exclude(status=Task.Status.DONE).filter(
        due_date__isnull=False, due_date__lt=today,
    ).count()

    total_projects = projects.count()
    team_members_count = User.objects.filter(is_active=True).count()

    recent_tasks = tasks.select_related("project", "assignee").order_by("-created_at")[:5]
    recent_activity = Activity.objects.select_related("actor", "project", "task")\
        .order_by("-created_at")[:8]

    top_projects = projects.annotate(
        total=Count("tasks"),
        done=Count("tasks", filter=Q(tasks__status=Task.Status.DONE)),
    ).order_by("-created_at")[:5]

    # 7-day series for the line chart
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    labels = [d.strftime("%a") for d in days]
    completed_series = []
    created_series = []
    for d in days:
        completed_series.append(
            tasks.filter(completed_at__date=d).count()
        )
        created_series.append(
            tasks.filter(created_at__date=d).count()
        )

    chart_data = {
        "labels": labels,
        "completed": completed_series,
        "created": created_series,
    }

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue_tasks,
        "total_projects": total_projects,
        "team_members_count": team_members_count,
        "recent_tasks": recent_tasks,
        "recent_activity": recent_activity,
        "top_projects": top_projects,
        "chart_data": chart_data,
    }
