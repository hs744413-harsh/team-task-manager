from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    CommentForm,
    ProjectForm,
    ProjectMemberAddForm,
    TaskForm,
)
from .models import Activity, Project, ProjectMembership, Task
from .permissions import (
    admin_required,
    can_edit_task,
    is_admin,
    is_project_member,
)
from .services import (
    dashboard_context,
    log_activity,
    visible_projects_for,
    visible_tasks_for,
)

User = get_user_model()


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
@login_required
def dashboard_view(request):
    context = dashboard_context(request.user)
    return render(request, "dashboard.html", context)


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #
@login_required
def project_list(request):
    qs = visible_projects_for(request.user).select_related("owner")\
        .prefetch_related("members").annotate(
            total=Count("tasks"),
            done=Count("tasks", filter=Q(tasks__status=Task.Status.DONE)),
        )

    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()
    ordering = request.GET.get("sort", "-created_at")

    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    if ordering in {"-created_at", "created_at", "name", "-name", "due_date"}:
        qs = qs.order_by(ordering)

    return render(request, "project_list.html", {
        "projects": qs,
        "search": search,
        "status": status,
        "priority": priority,
        "sort": ordering,
        "status_choices": Project.Status.choices,
        "priority_choices": Project.Priority.choices,
    })


@login_required
def project_create(request):
    if not is_admin(request.user):
        messages.error(request, "Only admins can create projects.")
        return redirect("project_list")

    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            form.save_m2m()
            # Always make the owner a manager-member.
            ProjectMembership.objects.get_or_create(
                project=project, user=request.user,
                defaults={"role": ProjectMembership.Role.MANAGER},
            )
            log_activity(request.user, Activity.Verb.CREATED_PROJECT,
                         project=project,
                         description=f"Created project '{project.name}'")
            messages.success(request, f"Project '{project.name}' created.")
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm()

    return render(request, "project_form.html",
                  {"form": form, "is_create": True})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.select_related("owner")
                       .prefetch_related("members", "tasks", "tasks__assignee"),
        pk=pk,
    )
    if not is_project_member(request.user, project):
        messages.error(request, "You don't have access to this project.")
        return redirect("project_list")

    tasks = project.tasks.select_related("assignee").all()
    member_form = ProjectMemberAddForm(project=project) if is_admin(request.user) else None

    return render(request, "project_detail.html", {
        "project": project,
        "tasks": tasks,
        "todo_tasks": tasks.filter(status=Task.Status.TODO),
        "in_progress_tasks": tasks.filter(status=Task.Status.IN_PROGRESS),
        "done_tasks": tasks.filter(status=Task.Status.DONE),
        "members": project.memberships.select_related("user"),
        "member_form": member_form,
        "can_manage": is_admin(request.user) or project.owner_id == request.user.id,
    })


@login_required
@admin_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            log_activity(request.user, Activity.Verb.UPDATED_PROJECT, project=project,
                         description=f"Updated project '{project.name}'")
            messages.success(request, "Project updated.")
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(request, "project_form.html",
                  {"form": form, "project": project, "is_create": False})


@login_required
@admin_required
@require_POST
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    name = project.name
    project.delete()
    messages.success(request, f"Project '{name}' deleted.")
    return redirect("project_list")


@login_required
@admin_required
@require_POST
def project_member_add(request, pk):
    project = get_object_or_404(Project, pk=pk)
    form = ProjectMemberAddForm(request.POST, project=project)
    if form.is_valid():
        user = form.cleaned_data["user"]
        ProjectMembership.objects.get_or_create(project=project, user=user)
        messages.success(request, f"{user.display_name} added to the project.")
    else:
        messages.error(request, "Could not add member.")
    return redirect("project_detail", pk=project.pk)


@login_required
@admin_required
@require_POST
def project_member_remove(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk)
    if user_id == project.owner_id:
        messages.error(request, "You can't remove the project owner.")
        return redirect("project_detail", pk=project.pk)
    ProjectMembership.objects.filter(project=project, user_id=user_id).delete()
    messages.success(request, "Member removed.")
    return redirect("project_detail", pk=project.pk)


# --------------------------------------------------------------------------- #
# Tasks
# --------------------------------------------------------------------------- #
@login_required
def task_board(request):
    tasks = visible_tasks_for(request.user).select_related("project", "assignee")
    project_id = request.GET.get("project")
    if project_id and project_id.isdigit():
        tasks = tasks.filter(project_id=int(project_id))

    todo = list(tasks.filter(status=Task.Status.TODO).order_by("-priority", "due_date"))
    in_progress = list(tasks.filter(status=Task.Status.IN_PROGRESS).order_by("-priority", "due_date"))
    done = list(tasks.filter(status=Task.Status.DONE).order_by("-completed_at"))

    columns = [
        {"code": Task.Status.TODO, "css": "todo",
         "label": "To Do", "tasks": todo, "count": len(todo)},
        {"code": Task.Status.IN_PROGRESS, "css": "in-progress",
         "label": "In Progress", "tasks": in_progress, "count": len(in_progress)},
        {"code": Task.Status.DONE, "css": "done",
         "label": "Completed", "tasks": done, "count": len(done)},
    ]

    return render(request, "task_board.html", {
        "columns": columns,
        "projects": visible_projects_for(request.user),
        "selected_project": int(project_id) if project_id and project_id.isdigit() else None,
    })


@login_required
def task_create(request):
    project_id = request.GET.get("project") or request.POST.get("project")
    project = None
    if project_id and str(project_id).isdigit():
        project = Project.objects.filter(pk=int(project_id)).first()
        if project and not is_project_member(request.user, project):
            messages.error(request, "You can't add tasks to that project.")
            return redirect("task_board")

    if request.method == "POST":
        form = TaskForm(request.POST, project=project, user=request.user)
        # Restrict project choices to projects the user can see.
        form.fields["project"].queryset = visible_projects_for(request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            if not is_project_member(request.user, task.project):
                messages.error(request, "You're not a member of that project.")
                return redirect("task_board")
            task.save()
            log_activity(request.user, Activity.Verb.CREATED_TASK,
                         project=task.project, task=task,
                         description=f"Created task '{task.title}'")
            messages.success(request, "Task created.")
            return redirect("project_detail", pk=task.project_id)
    else:
        form = TaskForm(project=project, user=request.user)
        form.fields["project"].queryset = visible_projects_for(request.user)

    return render(request, "task_form.html",
                  {"form": form, "is_create": True, "project": project})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task.objects.select_related("project"), pk=pk)
    if not can_edit_task(request.user, task):
        messages.error(request, "You can't edit this task.")
        return redirect("task_board")

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task, user=request.user)
        form.fields["project"].queryset = visible_projects_for(request.user)
        if form.is_valid():
            task = form.save()
            log_activity(request.user, Activity.Verb.UPDATED_TASK,
                         project=task.project, task=task,
                         description=f"Updated task '{task.title}'")
            messages.success(request, "Task updated.")
            return redirect("project_detail", pk=task.project_id)
    else:
        form = TaskForm(instance=task, user=request.user)
        form.fields["project"].queryset = visible_projects_for(request.user)

    return render(request, "task_form.html",
                  {"form": form, "is_create": False, "task": task})


@login_required
@require_POST
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not (is_admin(request.user) or task.created_by_id == request.user.id):
        messages.error(request, "You can't delete this task.")
        return redirect("task_board")
    project_id = task.project_id
    title = task.title
    task.delete()
    messages.success(request, f"Task '{title}' deleted.")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect("project_detail", pk=project_id)


@login_required
@require_POST
def task_status_update(request, pk):
    """Used by the Kanban drag-and-drop and inline status changes."""
    task = get_object_or_404(Task, pk=pk)
    if not can_edit_task(request.user, task):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "forbidden"}, status=403)
        messages.error(request, "You can't update that task.")
        return redirect("task_board")

    new_status = request.POST.get("status")
    if new_status not in dict(Task.Status.choices):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "invalid status"}, status=400)
        messages.error(request, "Invalid status.")
        return redirect("task_board")

    task.status = new_status
    task.save()

    verb = Activity.Verb.COMPLETED_TASK if new_status == Task.Status.DONE else Activity.Verb.UPDATED_TASK
    log_activity(request.user, verb, project=task.project, task=task,
                 description=f"{task.title} \u2192 {task.get_status_display()}")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "status": task.status})
    messages.success(request, f"Task moved to {task.get_status_display()}.")
    return redirect(request.META.get("HTTP_REFERER") or reverse("task_board"))


@login_required
@require_POST
def task_comment_create(request, pk):
    task = get_object_or_404(Task.objects.select_related("project"), pk=pk)
    if not is_project_member(request.user, task.project):
        messages.error(request, "You can't comment on this task.")
        return redirect("task_board")

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()
        log_activity(request.user, Activity.Verb.COMMENTED, project=task.project,
                     task=task, description=f"Commented on '{task.title}'")
        messages.success(request, "Comment added.")
    else:
        messages.error(request, "Comment cannot be empty.")

    return redirect("project_detail", pk=task.project_id)
