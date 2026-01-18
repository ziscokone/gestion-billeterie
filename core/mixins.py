"""
Mixins personnalisés pour les vues.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin qui requiert que l'utilisateur soit PDG ou Super Admin.
    Utilisé pour les pages de configuration globale.
    """

    def test_func(self):
        return self.request.user.has_global_access

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Vous n'avez pas les droits nécessaires pour accéder à cette page.")
        return super().handle_no_permission()


class GestionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin qui requiert que l'utilisateur soit PDG, Super Admin, Chef de Gare ou Guichetier.
    Utilisé pour les pages de gestion des voyages et recettes.
    Les chefs de gare et guichetiers ne verront que les données de leur gare.
    """

    def test_func(self):
        user = self.request.user
        return user.has_global_access or user.is_chef_gare or user.is_guichetier

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Vous n'avez pas les droits nécessaires pour accéder à cette page.")
        return super().handle_no_permission()
