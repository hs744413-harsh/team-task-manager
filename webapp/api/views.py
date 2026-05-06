from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tasks.models import Activity, Comment, Project, Task
from tasks.services import (
    dashboard_context,
    log_activity,
    visible_projects_for,
    visible_tasks_for,
)

from .permissions import (
    IsAssigneeOrProjectMember,
    IsCommentAuthorOrReadOnly,
    IsProjectMemberOrAdmin,
)
from .serializers import (
    CommentSerializer,
    DashboardStatsSerializer,
    ProjectSerializer,
    TaskSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsProjectMemberOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "priority", "owner"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name", "due_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return visible_projects_for(self.request.user).select_related("owner")\
            .prefetch_related("members")

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        log_activity(self.request.user, Activity.Verb.CREATED_PROJECT,
                     project=project, description=f"Created project '{project.name}'")

    def perform_update(self, serializer):
        project = serializer.save()
        log_activity(self.request.user, Activity.Verb.UPDATED_PROJECT,
                     project=project, description=f"Updated project '{project.name}'")


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsAssigneeOrProjectMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "priority", "project", "assignee"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "due_date", "priority"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return visible_tasks_for(self.request.user).select_related(
            "project", "assignee", "created_by"
        )

    def perform_create(self, serializer):
        task = serializer.save(created_by=self.request.user)
        log_activity(self.request.user, Activity.Verb.CREATED_TASK,
                     project=task.project, task=task,
                     description=f"Created task '{task.title}'")

    def perform_update(self, serializer):
        task = serializer.save()
        verb = (Activity.Verb.COMPLETED_TASK
                if task.status == Task.Status.DONE
                else Activity.Verb.UPDATED_TASK)
        log_activity(self.request.user, verb, project=task.project, task=task,
                     description=f"{task.title} \u2192 {task.get_status_display()}")


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["task"]

    def get_queryset(self):
        # Restrict to comments on tasks visible to the user.
        task_ids = visible_tasks_for(self.request.user).values_list("pk", flat=True)
        return Comment.objects.filter(task_id__in=task_ids).select_related(
            "author", "task"
        )

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        log_activity(self.request.user, Activity.Verb.COMMENTED,
                     project=comment.task.project, task=comment.task,
                     description=f"Commented on '{comment.task.title}'")


class DashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ctx = dashboard_context(request.user)
        payload = {
            "total_tasks": ctx["total_tasks"],
            "completed_tasks": ctx["completed_tasks"],
            "pending_tasks": ctx["pending_tasks"],
            "overdue_tasks": ctx["overdue_tasks"],
            "total_projects": ctx["total_projects"],
            "team_members_count": ctx["team_members_count"],
            "chart_data": ctx["chart_data"],
        }
        return Response(DashboardStatsSerializer(payload).data, status=status.HTTP_200_OK)
