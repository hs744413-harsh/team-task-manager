from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Project(models.Model):
    class Status(models.TextChoices):
        PLANNING = "PLANNING", "Planning"
        ACTIVE = "ACTIVE", "Active"
        ON_HOLD = "ON_HOLD", "On Hold"
        COMPLETED = "COMPLETED", "Completed"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNING)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ProjectMembership",
        related_name="projects",
        blank=True,
    )

    color = models.CharField(max_length=32, default="indigo",
                             help_text="One of: indigo, emerald, amber, rose, sky, violet")
    icon = models.CharField(max_length=64, default="folder",
                            help_text="Bootstrap Icons name without 'bi-' prefix")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_detail", args=[self.pk])

    @property
    def total_tasks(self) -> int:
        return self.tasks.count()

    @property
    def completed_tasks_count(self) -> int:
        return self.tasks.filter(status=Task.Status.DONE).count()

    @property
    def progress(self) -> int:
        total = self.total_tasks
        if not total:
            return 0
        return round(self.completed_tasks_count * 100 / total)

    @property
    def status_class(self) -> str:
        return {
            self.Status.PLANNING: "primary",
            self.Status.ACTIVE: "success",
            self.Status.ON_HOLD: "warning",
            self.Status.COMPLETED: "secondary",
        }.get(self.status, "secondary")

    @property
    def priority_class(self) -> str:
        return {
            self.Priority.LOW: "success",
            self.Priority.MEDIUM: "warning",
            self.Priority.HIGH: "danger",
        }.get(self.priority, "secondary")


class ProjectMembership(models.Model):
    class Role(models.TextChoices):
        MANAGER = "MANAGER", "Manager"
        MEMBER = "MEMBER", "Member"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="memberships")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user} on {self.project} ({self.role})"


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "TODO", "To Do"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        DONE = "DONE", "Completed"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)

    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_tasks",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tasks",
    )

    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Stamp completed_at the first time a task transitions to DONE so the
        # dashboard can chart "completed per day".
        if self.status == self.Status.DONE and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != self.Status.DONE and self.completed_at:
            self.completed_at = None
        super().save(*args, **kwargs)

    @property
    def is_overdue(self) -> bool:
        return bool(
            self.due_date
            and self.status != self.Status.DONE
            and self.due_date < timezone.now().date()
        )

    @property
    def status_class(self) -> str:
        return {
            self.Status.TODO: "primary",
            self.Status.IN_PROGRESS: "warning",
            self.Status.DONE: "success",
        }.get(self.status, "secondary")

    @property
    def priority_class(self) -> str:
        return {
            self.Priority.LOW: "success",
            self.Priority.MEDIUM: "warning",
            self.Priority.HIGH: "danger",
        }.get(self.priority, "secondary")


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="comments")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.task_id}"


class Activity(models.Model):
    """Append-only feed of meaningful actions for the dashboard/profile."""

    class Verb(models.TextChoices):
        CREATED_PROJECT = "CREATED_PROJECT", "created a project"
        UPDATED_PROJECT = "UPDATED_PROJECT", "updated a project"
        CREATED_TASK = "CREATED_TASK", "created a task"
        UPDATED_TASK = "UPDATED_TASK", "updated a task"
        COMPLETED_TASK = "COMPLETED_TASK", "completed a task"
        ASSIGNED_TASK = "ASSIGNED_TASK", "assigned a task"
        COMMENTED = "COMMENTED", "commented"

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name="activities")
    verb = models.CharField(max_length=32, choices=Verb.choices)
    project = models.ForeignKey(Project, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="activities")
    task = models.ForeignKey(Task, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name="activities")
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Activities"

    def __str__(self):
        return f"{self.actor} {self.get_verb_display()} - {self.description[:40]}"
