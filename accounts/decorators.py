# accounts/decorators.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')  # or your login URL name
        if request.user.user_type != 'admin':
            messages.error(request, "Access denied. Admin only.")
            return redirect('admin_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper