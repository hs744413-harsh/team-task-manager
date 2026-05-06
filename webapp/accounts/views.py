from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .forms import CustomUserCreationForm, ProfileUpdateForm
from .serializers import RegisterSerializer, UserSerializer


# --------------------------------------------------------------------------- #
# HTML views
# --------------------------------------------------------------------------- #
def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to TaskFlow, {user.first_name or user.username}!")
            return redirect("dashboard")
        messages.error(request, "Please fix the errors below and try again.")
    else:
        form = CustomUserCreationForm()
    return render(request, "register.html", {"form": form})


@login_required
def profile_view(request):
    """Read-only profile + activity feed."""
    user = request.user
    # Stats are computed lazily here so the profile page works even before
    # the tasks app has any data.
    projects_count = user.projects.count() if hasattr(user, "projects") else 0
    tasks_completed = (
        user.assigned_tasks.filter(status="DONE").count()
        if hasattr(user, "assigned_tasks") else 0
    )
    tasks_total = (
        user.assigned_tasks.count()
        if hasattr(user, "assigned_tasks") else 0
    )

    recent_activity = []
    try:
        from tasks.models import Activity
        recent_activity = Activity.objects.filter(actor=user).order_by("-created_at")[:8]
    except Exception:
        pass

    context = {
        "profile_user": user,
        "projects_count": projects_count,
        "tasks_completed": tasks_completed,
        "tasks_total": tasks_total,
        "recent_activity": recent_activity,
    }
    return render(request, "profile.html", context)


@login_required
def profile_edit_view(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
        messages.error(request, "Please fix the errors below.")
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, "profile_edit.html", {"form": form})


# --------------------------------------------------------------------------- #
# JWT / API
# --------------------------------------------------------------------------- #
class RegisterAPIView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    pass


class CustomTokenRefreshView(TokenRefreshView):
    pass


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
