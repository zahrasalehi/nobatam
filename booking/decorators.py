"""Decorator to require Paziresh24 OAuth session (no Django user)."""
import functools
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect


def require_paziresh24_login(view_func):
    """Redirect to login if session has no access_token."""

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.session.get('paziresh24_access_token'):
            return view_func(request, *args, **kwargs)
        next_url = request.get_full_path()
        login_url = settings.LOGIN_URL
        if next_url and next_url != login_url:
            return redirect(f"{login_url}?{urlencode({'next': next_url})}")
        return redirect(login_url)

    return wrapper
