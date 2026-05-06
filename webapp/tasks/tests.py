from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Activity, Project, ProjectMembership, Task

User = get_user_model()


class TaskAppTestCaseMixin:
    """Shared user setup for the test classes below."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="boss", email="boss@example.com",
            password="ZxcVbn!Pa55", role="ADMIN",
        )
        self.member = User.objects.create_user(
            username="worker", email="worker@example.com",
            password="ZxcVbn!Pa55", role="MEMBER",
        )
        self.outsider = User.objects.create_user(
            username="outsider", email="out@example.com",
            password="ZxcVbn!Pa55", role="MEMBER",
        )
        self.project = Project.objects.create(
            name="Demo", description="d", owner=self.admin,
        )
        ProjectMembership.objects.create(project=self.project, user=self.admin)
        ProjectMembership.objects.create(project=self.project, user=self.member)


class ProjectViewTests(TaskAppTestCaseMixin, TestCase):
    def test_member_cannot_create_project(self):
        c = Client()
        c.force_login(self.member)
        response = c.post(reverse("project_create"), {
            "name": "X", "description": "y",
            "status": "ACTIVE", "priority": "LOW",
            "color": "indigo", "icon": "folder",
        }, follow=True)
        self.assertFalse(Project.objects.filter(name="X").exists())
        # Redirected back to project list with an error message.
        self.assertEqual(response.status_code, 200)

    def test_admin_can_create_project(self):
        c = Client()
        c.force_login(self.admin)
        response = c.post(reverse("project_create"), {
            "name": "Cool", "description": "y",
            "status": "ACTIVE", "priority": "LOW",
            "color": "indigo", "icon": "folder",
        }, follow=True)
        self.assertTrue(Project.objects.filter(name="Cool").exists())
        self.assertEqual(response.status_code, 200)

    def test_project_detail_blocks_outsider(self):
        c = Client()
        c.force_login(self.outsider)
        response = c.get(reverse("project_detail", args=[self.project.pk]),
                         follow=True)
        # Redirected back to project list with error
        self.assertNotIn(self.project.name, response.content.decode())


class TaskViewTests(TaskAppTestCaseMixin, TestCase):
    def test_task_status_update_creates_activity(self):
        task = Task.objects.create(
            project=self.project, title="Ship it",
            created_by=self.member, assignee=self.member,
        )
        c = Client()
        c.force_login(self.member)
        response = c.post(
            reverse("task_status_update", args=[task.pk]),
            {"status": "DONE"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "DONE")
        self.assertIsNotNone(task.completed_at)
        self.assertTrue(Activity.objects.filter(verb="COMPLETED_TASK", task=task).exists())


class APITests(TaskAppTestCaseMixin, TestCase):
    def test_anon_cannot_list_projects(self):
        c = Client()
        response = c.get("/api/projects/")
        self.assertEqual(response.status_code, 401)

    def test_member_can_list_projects_via_api(self):
        c = Client()
        c.force_login(self.member)
        response = c.get("/api/projects/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["count"], 1)

    def test_dashboard_stats_endpoint(self):
        c = Client()
        c.force_login(self.admin)
        response = c.get("/api/dashboard/stats/")
        self.assertEqual(response.status_code, 200)
        for key in ("total_tasks", "completed_tasks", "pending_tasks",
                    "overdue_tasks", "total_projects", "team_members_count",
                    "chart_data"):
            self.assertIn(key, response.json())
