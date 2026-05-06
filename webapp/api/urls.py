from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CommentViewSet,
    DashboardStatsAPIView,
    ProjectViewSet,
    TaskViewSet,
)

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"comments", CommentViewSet, basename="comment")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/stats/", DashboardStatsAPIView.as_view(), name="api_dashboard_stats"),
]
