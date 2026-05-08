from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    """Decorator to restrict view access based on user roles"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """Decorator to restrict view access to admin users only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role != 'admin':
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_or_business_head_required(view_func):
    """Decorator to restrict view access to admin and business head users"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role not in ['admin', 'business_head']:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def business_head_required(view_func):
    """Decorator to restrict view access to business head and admin users"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role not in ['admin', 'business_head']:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def store_manager_required(view_func):
    """Decorator to restrict view access to store managers and team leaders only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role not in ['store_manager', 'team_leader']:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        if not request.user.assigned_store:
            messages.error(request, 'You are not assigned to any store.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def store_staff_required(view_func):
    """Decorator to restrict view access to store managers, team leaders, and store heads"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role not in ['store_manager', 'team_leader', 'store_head']:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        # Check if store head has managed stores or staff has assigned store
        if request.user.role == 'store_head':
            if not request.user.managed_stores.exists():
                messages.error(request, 'You are not assigned to manage any stores.')
                return redirect('dashboard')
        else:
            if not request.user.assigned_store:
                messages.error(request, 'You are not assigned to any store.')
                return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def reports_access_required(view_func):
    """Decorator to restrict reports access to admin, business head, and store head"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role not in ['admin', 'business_head', 'store_head']:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        # Check if store head has managed stores
        if request.user.role == 'store_head':
            if not request.user.managed_stores.exists():
                messages.error(request, 'You are not assigned to manage any stores.')
                return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper
