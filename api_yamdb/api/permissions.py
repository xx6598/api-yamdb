from rest_framework import permissions


class AdminOnly(permissions.BasePermission):
    """
    Разрешение только для администраторов и staff.
    """

    def has_permission(self, request, view):
        """Проверка разрешения на уровне запроса."""
        return (
                request.user.is_authenticated
                and (request.user.is_admin or request.user.is_staff)
        )

    def has_object_permission(self, request, view, obj):
        """Проверка разрешения на уровне объекта."""
        return (
                request.user.is_authenticated
                and (request.user.is_admin or request.user.is_staff)
        )


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Разрешение: чтение для всех, запись только для администраторов.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_authenticated and (request.user.is_admin
                                                  or request.user.is_superuser)


class AdminModeratorAuthorPermission(permissions.BasePermission):
    """
    Разрешение:
    - Чтение для всех
    - Создание для аутентифицированных
    - Изменение/удаление для автора, модератора или администратора
    """

    def has_permission(self, request, view):
        return (
                request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
                request.method in permissions.SAFE_METHODS
                or obj.author == request.user
                or request.user.is_moderator
                or request.user.is_admin

        )
