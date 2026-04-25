from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch


class Force2FAMiddleware:
    """
    Force les utilisateurs dont le rôle est dans ROLES_2FA_OBLIGATOIRE
    à configurer et utiliser la 2FA avant d'accéder à l'application.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._doit_forcer_2fa(request):
            return redirect(reverse('two_factor:setup'))
        return self.get_response(request)

    def _doit_forcer_2fa(self, request):
        user = request.user
        if not user.is_authenticated:
            return False

        roles_obligs = getattr(settings, 'ROLES_2FA_OBLIGATOIRE', [])
        role = getattr(user, 'role', None)
        if role not in roles_obligs:
            return False

        # L'utilisateur est déjà vérifié (a saisi son code OTP)
        if getattr(user, 'is_verified', lambda: False)():
            return False

        # A déjà un device configuré → il doit juste s'authentifier avec
        # (géré par two_factor:login, pas besoin de le rediriger vers setup)
        from django_otp import devices_for_user
        if list(devices_for_user(user, confirmed=True)):
            return False

        # Rôle obligatoire, pas de device → forcer la configuration
        try:
            setup_url = reverse('two_factor:setup')
            profile_url = reverse('two_factor:profile')
            qr_url = reverse('two_factor:qr')
        except NoReverseMatch:
            return False

        exempts = [
            setup_url,
            profile_url,
            qr_url,
            reverse('two_factor:login'),
            reverse('personnel:logout'),
        ]
        return request.path not in exempts
