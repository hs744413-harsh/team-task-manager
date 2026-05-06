from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

User = get_user_model()


class AuthFlowTests(TestCase):
    def test_register_creates_user_and_logs_in(self):
        c = Client()
        url = reverse("register")
        response = c.post(url, {
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Doe",
            "email": "alice@example.com",
            "password1": "ZxcVbn!Pa55",
            "password2": "ZxcVbn!Pa55",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="alice").exists())
        # Auto-login redirects to dashboard
        self.assertContains(response, "Dashboard")

    def test_register_requires_matching_passwords(self):
        c = Client()
        response = c.post(reverse("register"), {
            "username": "bob",
            "first_name": "Bob", "last_name": "X",
            "email": "bob@example.com",
            "password1": "ZxcVbn!Pa55", "password2": "different",
        })
        self.assertFalse(User.objects.filter(username="bob").exists())
        self.assertEqual(response.status_code, 200)

    def test_login_with_username(self):
        User.objects.create_user(
            username="charlie", email="charlie@example.com",
            password="ZxcVbn!Pa55",
        )
        c = Client()
        response = c.post(reverse("login"), {
            "username": "charlie", "password": "ZxcVbn!Pa55",
        }, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_logout_requires_post(self):
        user = User.objects.create_user(
            username="dave", email="dave@example.com", password="ZxcVbn!Pa55",
        )
        c = Client()
        c.force_login(user)
        # GET should NOT log out (Django 5 enforces POST)
        get_resp = c.get(reverse("logout"))
        self.assertIn(get_resp.status_code, (302, 405))
        post_resp = c.post(reverse("logout"))
        self.assertEqual(post_resp.status_code, 302)

    def test_dashboard_requires_login(self):
        c = Client()
        response = c.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
