from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Projects
    path("projects/", views.project_list, name="project_list"),
    path("projects/new/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("projects/<int:pk>/delete/", views.project_delete, name="project_delete"),
    path("projects/<int:pk>/members/add/", views.project_member_add, name="project_member_add"),
    path("projects/<int:pk>/members/<int:user_id>/remove/",
         views.project_member_remove, name="project_member_remove"),

    # Tasks
    path("tasks/", views.task_board, name="task_board"),
    path("tasks/new/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),
    path("tasks/<int:pk>/status/", views.task_status_update, name="task_status_update"),
    path("tasks/<int:pk>/comment/", views.task_comment_create, name="task_comment_create"),
]
