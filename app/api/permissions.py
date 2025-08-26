# app/api/permissions.py
from rest_framework import permissions
from django.core.exceptions import PermissionDenied
from functools import wraps

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактирование только администраторам, остальным - только чтение.
    """
    def has_permission(self, request, view):
        # Разрешить GET, HEAD или OPTIONS запросы всем
        if request.method in permissions.SAFE_METHODS:
            return True
        # Разрешить запись только администраторам
        return request.user and request.user.is_authenticated and request.user.role == 'admin'

class IsAdminOrStaff(permissions.BasePermission):
    """
    Разрешает доступ только администраторам и главным закупщикам.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'chief_purchaser']
        )

class IsPurchaserOrHigher(permissions.BasePermission):
    """
    Разрешает доступ закупщикам, главным закупщикам и администраторам.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'chief_purchaser', 'purchaser']
        )

    def has_object_permission(self, request, view, obj):
        # Предполагаем, что у объекта есть связь с организацией
        # и у пользователя есть профиль закупщика
        if request.user.role == 'admin':
            return True
        if hasattr(request.user, 'purchaser_profile'):
            user_profile = request.user.purchaser_profile
            # Проверка доступа к организации и городу объекта
            # (логика будет зависеть от типа объекта)
            # Например, для Product:
            if hasattr(obj, 'organization'):
                 return obj.organization in user_profile.organizations.all()
            # Для Price/PriceAlcohol нужно проверять организацию продукта/алкоголя
        return False # По умолчанию запрещено

# Оставим старые декораторы для совместимости или если они используются в других местах

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def chief_purchaser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ['admin', 'chief_purchaser']:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def purchaser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ['admin', 'chief_purchaser', 'purchaser']:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view