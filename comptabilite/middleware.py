from django.shortcuts import redirect
from django.conf import settings

class LoginRequiredMiddleware:
    """
    Redirige vers LOGIN_URL toute requête anonyme
    (sauf pour les urls de login, logout, static, admin…).
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [
            settings.LOGIN_URL.lstrip('/'),
            'logout',
            'admin',
            'static',
        ]

    def __call__(self, request):
        path = request.path_info.lstrip('/')
        if not request.user.is_authenticated:
            if not any(path.startswith(u) for u in self.exempt_urls):
                return redirect(settings.LOGIN_URL)
        return self.get_response(request)

# comptabilite/middleware.py
from django.utils import timezone
from comptabilite.models import UserProfile

class UpdateLastSeenMiddleware:
    THROTTLE_SECONDS = 300  # mise à jour au maximum toutes les 5 minutes

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            session_key = '_last_seen_ts'
            last_ts = request.session.get(session_key)
            if last_ts is None or (now.timestamp() - last_ts) >= self.THROTTLE_SECONDS:
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                profile.last_seen = now
                profile.save(update_fields=['last_seen'])
                request.session[session_key] = now.timestamp()
        return self.get_response(request)

