import secrets
from urllib.parse import urlencode

import requests as http_requests
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .models import GoogleProfile

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = request.GET.get('error')
    return render(request, 'home.html', {'error': error})


def login_view(request):
    state = secrets.token_hex(16)
    request.session['oauth_state'] = state

    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'scope': 'openid email profile',
        'response_type': 'code',
        'state': state,
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return redirect(auth_url)


def callback_view(request):
    error = request.GET.get('error')
    if error:
        return redirect(f"/?{urlencode({'error': 'oauth_error'})}")

    state = request.GET.get('state')
    session_state = request.session.pop('oauth_state', None)
    if state != session_state:
        return redirect('/?error=invalid_state')

    code = request.GET.get('code')

    token_response = http_requests.post(GOOGLE_TOKEN_URL, data={
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }, timeout=10)

    if not token_response.ok:
        return redirect('/?error=token_exchange_failed')

    access_token = token_response.json().get('access_token')
    if not access_token:
        return redirect('/?error=token_exchange_failed')

    userinfo_response = http_requests.get(GOOGLE_USERINFO_URL, headers={
        'Authorization': f'Bearer {access_token}'
    }, timeout=10)

    if not userinfo_response.ok:
        return redirect('/?error=userinfo_failed')

    userinfo = userinfo_response.json()
    google_id = userinfo.get('id')
    if not google_id:
        return redirect('/?error=missing_user_id')

    user, _ = User.objects.get_or_create(username=google_id)

    GoogleProfile.objects.update_or_create(
        user=user,
        defaults={
            'google_id': google_id,
            'name': userinfo.get('name', ''),
            'email': userinfo.get('email', ''),
            'picture': userinfo.get('picture', ''),
        }
    )

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('dashboard')


@login_required
def dashboard_view(request):
    profile = request.user.google_profile
    return render(request, 'dashboard.html', {'profile': profile})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('home')
