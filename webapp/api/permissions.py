from rest_framework.permissions import SAFE_METHODS, BasePermission

from tasks.permissions import is_admin, is_project_member


class IsAdminOrReadOnly(BasePermission):
    """Read for any authenticated user; write only for admins."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return is_admin(request.user)


class IsProjectMemberOrAdmin(BasePermission):
    """Project-level access: members can read; admins can write."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # `obj` is a Project instance.
        if request.method in SAFE_METHODS:
            return is_project_member(request.user, obj)
        return is_admin(request.user) or obj.owner_id == request.user.id


class IsAssigneeOrProjectMember(BasePermission):
    """Tasks: assignees and project members can edit; admins always can."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # `obj` is a Task instance.
        if request.method in SAFE_METHODS:
            return is_project_member(request.user, obj.project)
        if is_admin(request.user):
            return True
        if obj.assignee_id == request.user.id or obj.created_by_id == request.user.id:
            return True
        return obj.project.owner_id == request.user.id


class IsCommentAuthorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return is_project_member(request.user, obj.task.project)
        return is_admin(request.user) or obj.author_id == request.user.id
