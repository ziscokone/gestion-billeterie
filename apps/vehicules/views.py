from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from core.mixins import AdminRequiredMixin
from .models import ModeleVehicule, Vehicule
from .forms import ModeleVehiculeForm, VehiculeForm
from apps.compagnie.models import Compagnie


# Vues pour les modèles de véhicules
class ModeleVehiculeListView(AdminRequiredMixin, ListView):
    """Liste des modèles de véhicules."""
    model = ModeleVehicule
    template_name = 'vehicules/modele_list.html'
    context_object_name = 'modeles'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(marque__icontains=search)
            )
        return queryset.order_by('marque', 'nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ModeleVehiculeCreateView(AdminRequiredMixin, CreateView):
    """Créer un nouveau modèle de véhicule."""
    model = ModeleVehicule
    form_class = ModeleVehiculeForm
    template_name = 'vehicules/modele_form.html'
    success_url = reverse_lazy('vehicules:modele_list')

    def form_valid(self, form):
        messages.success(self.request, 'Modèle de véhicule créé avec succès.')
        return super().form_valid(form)


class ModeleVehiculeUpdateView(AdminRequiredMixin, UpdateView):
    """Modifier un modèle de véhicule."""
    model = ModeleVehicule
    form_class = ModeleVehiculeForm
    template_name = 'vehicules/modele_form.html'
    success_url = reverse_lazy('vehicules:modele_list')

    def form_valid(self, form):
        messages.success(self.request, 'Modèle de véhicule modifié avec succès.')
        return super().form_valid(form)


class ModeleVehiculeDeleteView(AdminRequiredMixin, DeleteView):
    """Supprimer un modèle de véhicule."""
    model = ModeleVehicule
    template_name = 'vehicules/modele_confirm_delete.html'
    success_url = reverse_lazy('vehicules:modele_list')

    def form_valid(self, form):
        messages.success(self.request, 'Modèle de véhicule supprimé avec succès.')
        return super().form_valid(form)


# Vues pour les véhicules
class VehiculeListView(AdminRequiredMixin, ListView):
    """Liste des véhicules."""
    model = Vehicule
    template_name = 'vehicules/vehicule_list.html'
    context_object_name = 'vehicules'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(immatriculation__icontains=search) |
                Q(modele__nom__icontains=search) |
                Q(modele__marque__icontains=search)
            )
        return queryset.select_related('modele').order_by('-actif', 'immatriculation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class VehiculeCreateView(AdminRequiredMixin, CreateView):
    """Créer un nouveau véhicule."""
    model = Vehicule
    form_class = VehiculeForm
    template_name = 'vehicules/vehicule_form.html'
    success_url = reverse_lazy('vehicules:vehicule_list')

    def form_valid(self, form):
        # Assigner automatiquement la compagnie
        compagnie = Compagnie.get_instance()
        if not compagnie:
            messages.error(self.request, 'Aucune compagnie n\'est configurée. Veuillez d\'abord créer une compagnie.')
            return self.form_invalid(form)
        form.instance.compagnie = compagnie
        messages.success(self.request, 'Véhicule créé avec succès.')
        return super().form_valid(form)


class VehiculeUpdateView(AdminRequiredMixin, UpdateView):
    """Modifier un véhicule."""
    model = Vehicule
    form_class = VehiculeForm
    template_name = 'vehicules/vehicule_form.html'
    success_url = reverse_lazy('vehicules:vehicule_list')

    def form_valid(self, form):
        messages.success(self.request, 'Véhicule modifié avec succès.')
        return super().form_valid(form)


class VehiculeDeleteView(AdminRequiredMixin, DeleteView):
    """Supprimer un véhicule."""
    model = Vehicule
    template_name = 'vehicules/vehicule_confirm_delete.html'
    success_url = reverse_lazy('vehicules:vehicule_list')

    def form_valid(self, form):
        messages.success(self.request, 'Véhicule supprimé avec succès.')
        return super().form_valid(form)
