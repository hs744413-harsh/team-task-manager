from django.contrib import admin

from .models import Activity, Comment, Project, ProjectMembership, Task


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1
    autocomplete_fields = ("user",)


class TaskInline(admin.TabularInline):
    model = Task
    fields = ("title", "status", "priority", "assignee", "due_date")
    autocomplete_fields = ("assignee",)
    extra = 0
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "priority", "due_date", "created_at")
    list_filter = ("status", "priority")
    search_fields = ("name", "description", "owner__username")
    autocomplete_fields = ("owner",)
    date_hierarchy = "created_at"
    inlines = [ProjectMembershipInline, TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "priority", "assignee",
                    "due_date", "created_at")
    list_filter = ("status", "priority", "project")
    search_fields = ("title", "description", "project__name", "assignee__username")
    autocomplete_fields = ("project", "assignee", "created_by")
    date_hierarchy = "created_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    search_fields = ("body", "author__username", "task__title")
    autocomplete_fields = ("task", "author")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "verb", "project", "task", "description")
    list_filter = ("verb",)
    search_fields = ("actor__username", "description")
    date_hierarchy = "created_at"


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "role", "joined_at")
    list_filter = ("role",)
    autocomplete_fields = ("project", "user")
