"""Populate the database with realistic demo data for screenshots/demos.

Usage:
    python manage.py seed_demo            # idempotent, safe to re-run
    python manage.py seed_demo --reset    # wipe project/task data first
"""

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from tasks.models import Activity, Comment, Project, ProjectMembership, Task

User = get_user_model()

DEMO_USERS = [
    ("admin", "Alice", "Admin", "alice@taskflow.local", "ADMIN"),
    ("john", "John", "Doe", "john@taskflow.local", "MEMBER"),
    ("sarah", "Sarah", "Johnson", "sarah@taskflow.local", "MEMBER"),
    ("mike", "Mike", "Chen", "mike@taskflow.local", "MEMBER"),
    ("emily", "Emily", "Wilson", "emily@taskflow.local", "MEMBER"),
]

DEMO_PROJECTS = [
    ("Website Redesign", "Complete overhaul of the company website with modern UI/UX.",
     "ACTIVE", "HIGH", "indigo", "palette"),
    ("Mobile App Development", "Cross-platform mobile app for iOS and Android.",
     "ACTIVE", "HIGH", "emerald", "phone"),
    ("API Integration", "Integrating third-party APIs and building RESTful services.",
     "ACTIVE", "MEDIUM", "amber", "plug"),
    ("Database Migration", "Migrate legacy database to cloud infrastructure.",
     "PLANNING", "MEDIUM", "sky", "database"),
    ("Security Audit", "Comprehensive security review across all systems.",
     "ON_HOLD", "HIGH", "rose", "shield-check"),
    ("Documentation Portal", "Knowledge base and developer docs.",
     "COMPLETED", "LOW", "violet", "file-earmark-text"),
]

DEMO_TASKS = [
    ("Design homepage mockup", "HIGH", "IN_PROGRESS", 5),
    ("Implement user authentication", "HIGH", "TODO", 8),
    ("Set up database schema", "MEDIUM", "DONE", -3),
    ("Write API documentation", "LOW", "TODO", 12),
    ("Security vulnerability scan", "HIGH", "IN_PROGRESS", 2),
    ("Optimize page load times", "MEDIUM", "TODO", 14),
    ("Add unit tests", "MEDIUM", "TODO", 7),
    ("Refactor data layer", "MEDIUM", "IN_PROGRESS", 6),
    ("Fix CSS regressions", "LOW", "DONE", -1),
    ("Wire up payment provider", "HIGH", "TODO", 10),
    ("Deploy staging environment", "MEDIUM", "DONE", -5),
    ("Create onboarding flow", "MEDIUM", "TODO", 9),
    ("Audit accessibility (a11y)", "MEDIUM", "TODO", 11),
    ("Set up CI pipeline", "HIGH", "DONE", -2),
    ("Write release notes", "LOW", "TODO", 15),
]


class Command(BaseCommand):
    help = "Seed the database with demo users, projects, tasks, comments, and activity."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Delete existing projects/tasks/activity before seeding.")

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Resetting existing demo data...")
            Activity.objects.all().delete()
            Comment.objects.all().delete()
            Task.objects.all().delete()
            ProjectMembership.objects.all().delete()
            Project.objects.all().delete()

        users = self._ensure_users()
        admin = next(u for u in users if u.role == User.Role.ADMIN)
        members = [u for u in users if u.role != User.Role.ADMIN]

        projects = self._ensure_projects(owner=admin, members=members)
        self._ensure_tasks(projects=projects, users=users)
        self._ensure_comments(users=users)

        self.stdout.write(self.style.SUCCESS(
            "Demo data ready. Login with admin/Admin12345 or any member with their "
            "username + password Member12345."
        ))

    # ----- helpers ---------------------------------------------------------- #
    def _ensure_users(self):
        created_users = []
        for username, first, last, email, role in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first,
                    "last_name": last,
                    "role": role,
                },
            )
            if created:
                user.set_password("Admin12345" if role == "ADMIN" else "Member12345")
                user.is_staff = (role == "ADMIN")
                user.is_superuser = (role == "ADMIN")
                user.save()
                self.stdout.write(f"  + user {user.username} ({role})")
            created_users.append(user)
        return created_users

    def _ensure_projects(self, owner, members):
        projects = []
        today = timezone.now().date()
        for i, (name, desc, status, priority, color, icon) in enumerate(DEMO_PROJECTS):
            project, created = Project.objects.get_or_create(
                name=name,
                defaults={
                    "description": desc,
                    "status": status,
                    "priority": priority,
                    "color": color,
                    "icon": icon,
                    "owner": owner,
                    "start_date": today - timedelta(days=30 + i * 5),
                    "due_date": today + timedelta(days=20 + i * 7),
                },
            )
            if created:
                self.stdout.write(f"  + project {name}")
                ProjectMembership.objects.get_or_create(
                    project=project, user=owner,
                    defaults={"role": ProjectMembership.Role.MANAGER},
                )
                for m in random.sample(members, k=min(3, len(members))):
                    ProjectMembership.objects.get_or_create(
                        project=project, user=m,
                        defaults={"role": ProjectMembership.Role.MEMBER},
                    )
                Activity.objects.create(
                    actor=owner, verb=Activity.Verb.CREATED_PROJECT, project=project,
                    description=f"Created project '{name}'",
                )
            projects.append(project)
        return projects

    def _ensure_tasks(self, projects, users):
        today = timezone.now().date()
        for i, (title, priority, status, day_offset) in enumerate(DEMO_TASKS):
            project = projects[i % len(projects)]
            assignee = random.choice(users)
            task, created = Task.objects.get_or_create(
                project=project,
                title=title,
                defaults={
                    "description": f"{title} for {project.name}.",
                    "status": status,
                    "priority": priority,
                    "assignee": assignee,
                    "created_by": project.owner,
                    "due_date": today + timedelta(days=day_offset),
                },
            )
            if created and status == "DONE":
                # Use raw update so save() doesn't reset completed_at to "now"
                Task.objects.filter(pk=task.pk).update(
                    completed_at=timezone.now() - timedelta(days=abs(day_offset))
                )
            if created:
                Activity.objects.create(
                    actor=project.owner, verb=Activity.Verb.CREATED_TASK,
                    project=project, task=task,
                    description=f"Created task '{title}'",
                )

    def _ensure_comments(self, users):
        sample_bodies = [
            "Looks good — kicking this off.",
            "Blocked on the design review.",
            "I'll handle this by EOD Friday.",
            "Pushed an update, please re-review.",
            "Adding more context in the ticket.",
        ]
        for task in Task.objects.order_by("?")[:6]:
            for _ in range(random.randint(1, 2)):
                Comment.objects.get_or_create(
                    task=task,
                    author=random.choice(users),
                    body=random.choice(sample_bodies),
                )
