from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import path, include


def root(request):
    """Send authenticated users to the dashboard, others to login."""
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", root, name="landing"),
    path("accounts/", include("accounts.urls")),
    path("api/", include("api.urls")),
    path("", include("tasks.urls")),

    # Built-in password-reset flow (named URLs that templates already reference)
    path("password-reset/",
         auth_views.PasswordResetView.as_view(template_name="auth/password_reset.html"),
         name="password_reset"),
    path("password-reset/done/",
         auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"),
         name="password_reset_done"),
    path("reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(template_name="auth/password_reset_confirm.html"),
         name="password_reset_confirm"),
    path("reset/done/",
         auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"),
         name="password_reset_complete"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
