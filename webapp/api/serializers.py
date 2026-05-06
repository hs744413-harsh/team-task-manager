from rest_framework import serializers

from accounts.serializers import UserMiniSerializer
from tasks.models import Comment, Project, ProjectMembership, Task


class ProjectMembershipSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ("id", "user", "role", "joined_at")


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserMiniSerializer(read_only=True)
    members = UserMiniSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, required=False,
        queryset=Project._meta.get_field("members").related_model.objects.all(),
        source="members",
    )
    progress = serializers.IntegerField(read_only=True)
    total_tasks = serializers.IntegerField(read_only=True)
    completed_tasks_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = (
            "id", "name", "description", "status", "priority",
            "start_date", "due_date", "color", "icon",
            "owner", "members", "member_ids",
            "progress", "total_tasks", "completed_tasks_count",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "owner", "created_at", "updated_at")


class TaskSerializer(serializers.ModelSerializer):
    assignee = UserMiniSerializer(read_only=True)
    created_by = UserMiniSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        write_only=True, required=False, allow_null=True,
        queryset=Project._meta.get_field("members").related_model.objects.all(),
        source="assignee",
    )
    project_name = serializers.CharField(source="project.name", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id", "project", "project_name", "title", "description",
            "status", "priority", "assignee", "assignee_id", "created_by",
            "due_date", "completed_at", "is_overdue",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "completed_at",
                            "created_at", "updated_at")


class CommentSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "task", "author", "body", "created_at")
        read_only_fields = ("id", "author", "created_at")


class DashboardStatsSerializer(serializers.Serializer):
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    total_projects = serializers.IntegerField()
    team_members_count = serializers.IntegerField()
    chart_data = serializers.DictField()
