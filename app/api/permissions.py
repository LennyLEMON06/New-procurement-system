# permissions.py
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import get_object_or_404

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