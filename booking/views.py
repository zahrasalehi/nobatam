import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse

from .decorators import require_paziresh24_login
from .paziresh24_client import Paziresh24APIError, get_api_client
from .services import book_first_available


def _auth_url(state: str) -> str:
    params = {
        'client_id': settings.PAZIRESH24_CLIENT_ID,
        'response_type': 'code',
        'scope': settings.PAZIRESH24_SCOPE,
        'redirect_uri': settings.PAZIRESH24_REDIRECT_URI,
        'state': state,
        'kc_idp_hint': 'gozar',
        'skip_prompt': 'true',
    }
    base = settings.PAZIRESH24_AUTH_BASE.rstrip('/')
    return f"{base}/auth?{urlencode(params)}"


def login_redirect(request):
    """Redirect user to Paziresh24 OAuth authorize URL."""
    state = secrets.token_urlsafe(32)
    request.session['paziresh24_oauth_state'] = state
    next_url = request.GET.get('next')
    if next_url:
        request.session['paziresh24_oauth_next'] = next_url
    url = _auth_url(state)
    return redirect(url)


def auth_callback(request):
    """Handle redirect from Paziresh24: exchange code for token, store in session."""
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')

    if error:
        return render(request, 'booking/error.html', {
            'message': f'احراز هویت ناموفق: {error}',
        }, status=400)

    if not code:
        return render(request, 'booking/error.html', {
            'message': 'کد احراز هویت دریافت نشد.',
        }, status=400)

    saved_state = request.session.pop('paziresh24_oauth_state', None)
    if not saved_state or state != saved_state:
        return render(request, 'booking/error.html', {
            'message': 'وضعیت (state) نامعتبر. لطفاً دوباره وارد شوید.',
        }, status=400)

    token_url = f"{settings.PAZIRESH24_AUTH_BASE.rstrip('/')}/token"
    data = {
        'grant_type': 'authorization_code',
        'client_id': settings.PAZIRESH24_CLIENT_ID,
        'client_secret': settings.PAZIRESH24_CLIENT_SECRET,
        'redirect_uri': settings.PAZIRESH24_REDIRECT_URI,
        'code': code,
    }
    headers = {'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        resp = requests.post(token_url, data=data, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        return render(request, 'booking/error.html', {
            'message': f'دریافت توکن ناموفق: {e}',
        }, status=502)

    body = resp.json()
    access_token = body.get('access_token')
    if not access_token:
        return render(request, 'booking/error.html', {
            'message': 'توکن دسترسی در پاسخ دریافت نشد.',
        }, status=502)

    request.session['paziresh24_access_token'] = access_token
    request.session['paziresh24_refresh_token'] = body.get('refresh_token') or ''
    request.session['paziresh24_expires_in'] = body.get('expires_in')

    next_url = request.session.pop('paziresh24_oauth_next', None) or request.GET.get('next') or reverse('booking:dashboard')
    return redirect(next_url)


def logout_view(request):
    """Clear Paziresh24 token from session."""
    request.session.flush()
    return redirect(reverse('booking:home'))


def home(request):
    """Landing: show Login with Paziresh24 if not logged in, else redirect to dashboard."""
    if request.session.get('paziresh24_access_token'):
        return redirect(reverse('booking:dashboard'))
    return render(request, 'booking/home.html')


@require_paziresh24_login
def dashboard(request):
    """Dashboard after login: search and book first available."""
    return render(request, 'booking/dashboard.html')


@require_paziresh24_login
def search(request):
    """Search doctors; show results and allow selecting provider."""
    q = (request.GET.get('q') or '').strip()
    if not q:
        return render(request, 'booking/search.html', {'query': '', 'results': None})

    client = get_api_client(request)
    try:
        data = client.search(text=q)
    except Paziresh24APIError as e:
        if e.status_code == 401:
            request.session.flush()
            return redirect(f"{reverse('booking:login')}?next={request.get_full_path()}")
        return render(request, 'booking/error.html', {
            'message': f'خطا در جستجو: {e}',
        }, status=e.status_code or 500)

    results = data.get('search', {}).get('result') or []
    return render(request, 'booking/search.html', {
        'query': q,
        'results': results,
    })


@require_paziresh24_login
def book_first_available_view(request):
    """Book the first available slot for the selected provider (provider_id in POST)."""
    provider_id = (request.POST.get('provider_id') or request.GET.get('provider_id') or '').strip()
    if not provider_id:
        return render(request, 'booking/error.html', {
            'message': 'پزشک انتخاب نشده است.',
        }, status=400)

    client = get_api_client(request)
    try:
        appointment = book_first_available(client, provider_id)
    except Paziresh24APIError as e:
        if e.status_code == 401:
            request.session.flush()
            return redirect(f"{reverse('booking:login')}?next={request.get_full_path()}")
        if e.status_code == 409:
            return render(request, 'booking/error.html', {
                'message': 'این نوبت قبلاً رزرو شده است. لطفاً دوباره جستجو کنید.',
            }, status=409)
        return render(request, 'booking/error.html', {
            'message': f'خطا در رزرو نوبت: {e}',
        }, status=e.status_code or 500)

    return render(request, 'booking/book_success.html', {'appointment': appointment})
