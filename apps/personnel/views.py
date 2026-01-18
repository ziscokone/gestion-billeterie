from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from core.mixins import AdminRequiredMixin
from .models import Utilisateur, Chauffeur, Convoyeur
from .forms import UtilisateurForm, ChauffeurForm, ConvoyeurForm
from apps.compagnie.models import Compagnie


# Vues pour les utilisateurs
class UtilisateurListView(AdminRequiredMixin, ListView):
    """Liste des utilisateurs."""
    model = Utilisateur
    template_name = 'personnel/utilisateur_list.html'
    context_object_name = 'utilisateurs'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(nom_complet__icontains=search) |
                Q(username__icontains=search) |
                Q(telephone__icontains=search)
            )
        return queryset.select_related('gare').order_by('nom_complet')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
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


# Vues pour les chauffeurs
class ChauffeurListView(AdminRequiredMixin, ListView):
    """Liste des chauffeurs."""
    model = Chauffeur
    template_name = 'personnel/chauffeur_list.html'
    context_object_name = 'chauffeurs'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(nom_complet__icontains=search) |
                Q(numero_permis__icontains=search) |
                Q(telephone__icontains=search)
            )
        return queryset.order_by('nom_complet')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
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
