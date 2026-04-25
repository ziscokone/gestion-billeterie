from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
from core.mixins import AdminRequiredMixin
from .models import Utilisateur, Chauffeur, Convoyeur
from .forms import UtilisateurForm, ChauffeurForm, ConvoyeurForm
from apps.compagnie.models import Compagnie
import json
from datetime import date


# Vues pour les utilisateurs
class UtilisateurListView(AdminRequiredMixin, ListView):
    """Liste des utilisateurs."""
    model = Utilisateur
    template_name = 'personnel/utilisateur_list.html'
    context_object_name = 'utilisateurs'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        role   = self.request.GET.get('role', 'tous')
        if search:
            queryset = queryset.filter(
                Q(nom_complet__icontains=search) |
                Q(username__icontains=search) |
                Q(telephone__icontains=search)
            )
        if role != 'tous':
            queryset = queryset.filter(role=role)
        return queryset.select_related('gare').order_by('nom_complet')

    def get_context_data(self, **kwargs):
        from django_otp import devices_for_user
        from django.conf import settings
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['role_filtre']  = self.request.GET.get('role', 'tous')
        context['nb_total']     = Utilisateur.objects.count()
        context['nb_actifs']    = Utilisateur.objects.filter(actif=True).count()
        context['nb_inactifs']  = Utilisateur.objects.filter(actif=False).count()
        roles_2fa = getattr(settings, 'ROLES_2FA_OBLIGATOIRE', [])
        context['roles_2fa'] = roles_2fa
        # Dictionnaire {user_id: 'active'|'inactive'|'none'}
        statuts_2fa = {}
        for u in context['utilisateurs']:
            if u.role in roles_2fa:
                a_device = bool(list(devices_for_user(u, confirmed=True)))
                statuts_2fa[u.pk] = 'active' if a_device else 'inactive'
            else:
                statuts_2fa[u.pk] = 'none'
        context['statuts_2fa'] = statuts_2fa
        return context


class UtilisateurCreateView(AdminRequiredMixin, CreateView):
    """Créer un nouvel utilisateur."""
    model = Utilisateur
    form_class = UtilisateurForm
    template_name = 'personnel/utilisateur_form.html'
    success_url = reverse_lazy('personnel:utilisateur_list')

    def form_valid(self, form):
        messages.success(self.request, 'Utilisateur créé avec succès.')
        return super().form_valid(form)


class UtilisateurUpdateView(AdminRequiredMixin, UpdateView):
    """Modifier un utilisateur."""
    model = Utilisateur
    form_class = UtilisateurForm
    template_name = 'personnel/utilisateur_form.html'
    success_url = reverse_lazy('personnel:utilisateur_list')

    def form_valid(self, form):
        messages.success(self.request, 'Utilisateur modifié avec succès.')
        return super().form_valid(form)


class UtilisateurDeleteView(AdminRequiredMixin, DeleteView):
    """Supprimer un utilisateur."""
    model = Utilisateur
    template_name = 'personnel/utilisateur_confirm_delete.html'
    success_url = reverse_lazy('personnel:utilisateur_list')

    def form_valid(self, form):
        messages.success(self.request, 'Utilisateur supprimé avec succès.')
        return super().form_valid(form)


class Reset2FAView(LoginRequiredMixin, View):
    """Réinitialise la 2FA d'un utilisateur. Réservé aux super_admin."""

    def post(self, request, pk):
        if request.user.role != 'super_admin':
            raise PermissionDenied

        cible = get_object_or_404(Utilisateur, pk=pk)
        self._supprimer_devices(cible)

        if cible.pk == request.user.pk:
            messages.success(request, f'Votre 2FA a été réinitialisée. Reconfigurez-la à votre prochaine connexion.')
        else:
            messages.success(request, f'La 2FA de {cible.nom_complet} a été réinitialisée avec succès.')

        return redirect('personnel:utilisateur_list')

    def _supprimer_devices(self, user):
        from django_otp.plugins.otp_totp.models import TOTPDevice
        from django_otp.plugins.otp_static.models import StaticDevice
        TOTPDevice.objects.filter(user=user).delete()
        StaticDevice.objects.filter(user=user).delete()


# Vues pour les chauffeurs
class ChauffeurListView(AdminRequiredMixin, ListView):
    """Liste des chauffeurs."""
    model = Chauffeur
    template_name = 'personnel/chauffeur_list.html'
    context_object_name = 'chauffeurs'

    def get_queryset(self):
        from django.db.models import Count
        queryset = super().get_queryset().annotate(nb_voyages=Count('voyages'))
        search  = self.request.GET.get('q')
        statut  = self.request.GET.get('statut', 'tous')
        if search:
            queryset = queryset.filter(
                Q(nom_complet__icontains=search) |
                Q(numero_permis__icontains=search) |
                Q(telephone__icontains=search)
            )
        if statut == 'actifs':
            queryset = queryset.filter(actif=True)
        elif statut == 'inactifs':
            queryset = queryset.filter(actif=False)
        return queryset.order_by('nom_complet')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['statut_filtre'] = self.request.GET.get('statut', 'tous')
        context['nb_total']    = Chauffeur.objects.count()
        context['nb_actifs']   = Chauffeur.objects.filter(actif=True).count()
        context['nb_inactifs'] = Chauffeur.objects.filter(actif=False).count()
        return context


class ChauffeurCreateView(AdminRequiredMixin, CreateView):
    """Créer un nouveau chauffeur."""
    model = Chauffeur
    form_class = ChauffeurForm
    template_name = 'personnel/chauffeur_form.html'
    success_url = reverse_lazy('personnel:chauffeur_list')

    def form_valid(self, form):
        form.instance.compagnie = Compagnie.get_instance()
        messages.success(self.request, 'Chauffeur créé avec succès.')
        return super().form_valid(form)


class ChauffeurUpdateView(AdminRequiredMixin, UpdateView):
    """Modifier un chauffeur."""
    model = Chauffeur
    form_class = ChauffeurForm
    template_name = 'personnel/chauffeur_form.html'
    success_url = reverse_lazy('personnel:chauffeur_list')

    def form_valid(self, form):
        messages.success(self.request, 'Chauffeur modifié avec succès.')
        return super().form_valid(form)


class ChauffeurDeleteView(AdminRequiredMixin, DeleteView):
    """Supprimer un chauffeur."""
    model = Chauffeur
    template_name = 'personnel/chauffeur_confirm_delete.html'
    success_url = reverse_lazy('personnel:chauffeur_list')

    def form_valid(self, form):
        messages.success(self.request, 'Chauffeur supprimé avec succès.')
        return super().form_valid(form)


class ChauffeurDetailView(AdminRequiredMixin, DetailView):
    """Fiche détail d'un chauffeur avec son activité voyages."""
    model = Chauffeur
    template_name = 'personnel/chauffeur_detail.html'
    context_object_name = 'chauffeur'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chauffeur = self.object
        today = date.today()

        # Filtres période (défaut : année en cours)
        date_debut = self.request.GET.get('date_debut') or date(today.year, 1, 1).strftime('%Y-%m-%d')
        date_fin   = self.request.GET.get('date_fin')   or today.strftime('%Y-%m-%d')
        context['date_debut'] = date_debut
        context['date_fin']   = date_fin

        # Tous les voyages du chauffeur
        tous_voyages = chauffeur.voyages.all()

        # Voyages sur la période filtrée
        voyages_periode = tous_voyages.filter(
            date_depart__gte=date_debut,
            date_depart__lte=date_fin
        ).select_related('gare', 'ligne', 'vehicule').order_by('-date_depart', '-heure_depart')

        context['voyages']           = voyages_periode
        context['nb_voyages_periode'] = voyages_periode.count()
        context['nb_total']           = tous_voyages.count()
        context['nb_termines']        = voyages_periode.filter(statut='termine').count()
        context['nb_annules']         = voyages_periode.filter(statut='annule').count()

        # Voyages ce mois
        debut_mois = today.replace(day=1)
        context['nb_ce_mois'] = tous_voyages.filter(date_depart__gte=debut_mois).count()

        # Dernier voyage
        context['dernier_voyage'] = tous_voyages.order_by('-date_depart').first()

        # Graphique : voyages par mois sur les 12 derniers mois
        mois_labels = []
        mois_data   = []
        for i in range(11, -1, -1):
            month = today.month - i
            year  = today.year
            while month <= 0:
                month += 12
                year  -= 1
            debut = date(year, month, 1)
            fin   = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
            count = tous_voyages.filter(date_depart__gte=debut, date_depart__lt=fin).count()
            mois_labels.append(debut.strftime('%b %Y'))
            mois_data.append(count)

        context['chart_labels_json'] = json.dumps(mois_labels)
        context['chart_data_json']   = json.dumps(mois_data)
        return context


# Vues pour les convoyeurs
class ConvoyeurListView(AdminRequiredMixin, ListView):
    """Liste des convoyeurs."""
    model = Convoyeur
    template_name = 'personnel/convoyeur_list.html'
    context_object_name = 'convoyeurs'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(nom_complet__icontains=search) |
                Q(telephone__icontains=search)
            )
        return queryset.order_by('nom_complet')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ConvoyeurCreateView(AdminRequiredMixin, CreateView):
    """Créer un nouveau convoyeur."""
    model = Convoyeur
    form_class = ConvoyeurForm
    template_name = 'personnel/convoyeur_form.html'
    success_url = reverse_lazy('personnel:convoyeur_list')

    def form_valid(self, form):
        form.instance.compagnie = Compagnie.get_instance()
        messages.success(self.request, 'Convoyeur créé avec succès.')
        return super().form_valid(form)


class ConvoyeurUpdateView(AdminRequiredMixin, UpdateView):
    """Modifier un convoyeur."""
    model = Convoyeur
    form_class = ConvoyeurForm
    template_name = 'personnel/convoyeur_form.html'
    success_url = reverse_lazy('personnel:convoyeur_list')

    def form_valid(self, form):
        messages.success(self.request, 'Convoyeur modifié avec succès.')
        return super().form_valid(form)


class ConvoyeurDeleteView(AdminRequiredMixin, DeleteView):
    """Supprimer un convoyeur."""
    model = Convoyeur
    template_name = 'personnel/convoyeur_confirm_delete.html'
    success_url = reverse_lazy('personnel:convoyeur_list')

    def form_valid(self, form):
        messages.success(self.request, 'Convoyeur supprimé avec succès.')
        return super().form_valid(form)
