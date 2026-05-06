from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Session-based auth (browser)
    path("login/",
         auth_views.LoginView.as_view(template_name="login.html",
                                      redirect_authenticated_user=True),
         name="login"),
    # Django 5 LogoutView only accepts POST; the sidebar/dropdown submit a
    # tiny CSRF-protected form to this URL.
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("register/", views.register_view, name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),

    # JWT (API consumers)
    path("api/token/", views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", views.CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("api/register/", views.RegisterAPIView.as_view(), name="api_register"),
    path("api/me/", views.MeAPIView.as_view(), name="api_me"),
]
