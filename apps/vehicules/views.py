from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime, timedelta
from core.mixins import AdminRequiredMixin
from .models import ModeleVehicule, Vehicule, ReparationVehicule, TypeReparation
from .forms import ModeleVehiculeForm, VehiculeForm, ReparationVehiculeForm, TypeReparationForm
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


# Vues pour les réparations
class ReparationVehiculeListView(AdminRequiredMixin, ListView):
    """Liste de toutes les réparations."""
    model = ReparationVehicule
    template_name = 'vehicules/reparation_list.html'
    context_object_name = 'reparations'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtre par véhicule
        vehicule_id = self.request.GET.get('vehicule')
        if vehicule_id:
            queryset = queryset.filter(vehicule_id=vehicule_id)

        # Filtre par type
        type_reparation = self.request.GET.get('type')
        if type_reparation:
            queryset = queryset.filter(type_reparation_id=type_reparation)

        # Filtre par statut
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)

        # Filtre par date
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        if date_debut:
            queryset = queryset.filter(date_reparation__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_reparation__lte=date_fin)

        return queryset.select_related('vehicule', 'vehicule__modele', 'type_reparation').order_by('-date_reparation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicules'] = Vehicule.objects.all().order_by('immatriculation')
        context['types_reparation'] = TypeReparation.objects.filter(actif=True)
        context['statuts'] = ReparationVehicule.STATUT_CHOICES

        # Calcul du total pour la période filtrée
        queryset = self.get_queryset()
        context['cout_total_periode'] = queryset.aggregate(total=Sum('montant'))['total'] or 0

        # Récupérer les valeurs des filtres
        context['vehicule_filtre'] = self.request.GET.get('vehicule', '')
        context['type_filtre'] = self.request.GET.get('type', '')
        context['statut_filtre'] = self.request.GET.get('statut', '')
        context['date_debut_filtre'] = self.request.GET.get('date_debut', '')
        context['date_fin_filtre'] = self.request.GET.get('date_fin', '')

        return context


class ReparationVehiculeCreateView(AdminRequiredMixin, CreateView):
    """Créer une nouvelle réparation."""
    model = ReparationVehicule
    form_class = ReparationVehiculeForm
    template_name = 'vehicules/reparation_form.html'

    def get_initial(self):
        initial = super().get_initial()
        # Pré-remplir le véhicule si passé en paramètre
        vehicule_id = self.request.GET.get('vehicule')
        if vehicule_id:
            initial['vehicule'] = vehicule_id
        return initial

    def get_success_url(self):
        # Rediriger vers la page de modification du véhicule si venant de là
        if self.request.GET.get('from_vehicule'):
            return reverse_lazy('vehicules:vehicule_update', kwargs={'pk': self.object.vehicule.pk})
        return reverse_lazy('vehicules:reparation_list')

    def form_valid(self, form):
        messages.success(self.request, 'Réparation enregistrée avec succès.')
        return super().form_valid(form)


class ReparationVehiculeDetailView(AdminRequiredMixin, DetailView):
    """Détails d'une réparation."""
    model = ReparationVehicule
    template_name = 'vehicules/reparation_detail.html'
    context_object_name = 'reparation'


class ReparationVehiculeUpdateView(AdminRequiredMixin, UpdateView):
    """Modifier une réparation."""
    model = ReparationVehicule
    form_class = ReparationVehiculeForm
    template_name = 'vehicules/reparation_form.html'

    def get_success_url(self):
        return reverse_lazy('vehicules:reparation_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Réparation modifiée avec succès.')
        return super().form_valid(form)


class ReparationVehiculeDeleteView(AdminRequiredMixin, DeleteView):
    """Supprimer une réparation."""
    model = ReparationVehicule
    template_name = 'vehicules/reparation_confirm_delete.html'
    success_url = reverse_lazy('vehicules:reparation_list')

    def form_valid(self, form):
        messages.success(self.request, 'Réparation supprimée avec succès.')
        return super().form_valid(form)


# Vue pour le rapport analytique
class RapportReparationsView(AdminRequiredMixin, TemplateView):
    """Rapport analytique des réparations véhicules."""
    template_name = 'vehicules/rapport_reparations.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupérer les filtres de date
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')

        # Par défaut, les 12 derniers mois
        if not date_debut:
            date_debut = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not date_fin:
            date_fin = datetime.now().strftime('%Y-%m-%d')

        context['date_debut'] = date_debut
        context['date_fin'] = date_fin

        # Requête filtrée
        reparations = ReparationVehicule.objects.filter(
            date_reparation__gte=date_debut,
            date_reparation__lte=date_fin
        )

        # Statistiques globales
        context['cout_total'] = reparations.aggregate(total=Sum('montant'))['total'] or 0
        context['nb_reparations'] = reparations.count()
        context['nb_vehicules'] = reparations.values('vehicule').distinct().count()

        # Statistiques par véhicule
        vehicules_stats = []
        for vehicule in Vehicule.objects.all():
            reparations_vehicule = reparations.filter(vehicule=vehicule)
            cout_total = reparations_vehicule.aggregate(total=Sum('montant'))['total'] or 0
            nb_reparations = reparations_vehicule.count()

            if nb_reparations > 0:
                cout_moyen = cout_total / nb_reparations

                # Déterminer le niveau d'alerte
                if cout_total > 2000000:
                    niveau_alerte = 'critique'
                elif cout_total > 1000000:
                    niveau_alerte = 'surveillance'
                else:
                    niveau_alerte = 'normal'

                vehicules_stats.append({
                    'vehicule': vehicule,
                    'cout_total': cout_total,
                    'nb_reparations': nb_reparations,
                    'cout_moyen': cout_moyen,
                    'niveau_alerte': niveau_alerte
                })

        # Trier par coût total décroissant
        vehicules_stats.sort(key=lambda x: x['cout_total'], reverse=True)
        context['vehicules_stats'] = vehicules_stats

        # Répartition par type de réparation
        types_stats = []
        cout_total_types = context['cout_total']
        for type_rep in TypeReparation.objects.filter(actif=True):
            cout = reparations.filter(type_reparation=type_rep).aggregate(total=Sum('montant'))['total'] or 0
            if cout > 0:
                pourcentage = (cout / cout_total_types * 100) if cout_total_types > 0 else 0
                types_stats.append({
                    'label': type_rep.nom,
                    'cout': cout,
                    'pourcentage': pourcentage
                })

        context['types_stats'] = types_stats
        context['types_stats_json'] = json.dumps([
            {'label': t['label'], 'cout': float(t['cout']), 'pourcentage': round(t['pourcentage'], 1)}
            for t in types_stats
        ])

        # Véhicules critiques (> 2M)
        context['vehicules_critiques'] = [v for v in vehicules_stats if v['niveau_alerte'] == 'critique']

        return context


# Vues pour les types de réparation
class TypeReparationListView(AdminRequiredMixin, ListView):
    """Liste des types de réparation."""
    model = TypeReparation
    template_name = 'vehicules/type_reparation_list.html'
    context_object_name = 'types_reparation'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset.order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class TypeReparationCreateView(AdminRequiredMixin, CreateView):
    """Créer un nouveau type de réparation."""
    model = TypeReparation
    form_class = TypeReparationForm
    template_name = 'vehicules/type_reparation_form.html'
    success_url = reverse_lazy('vehicules:type_reparation_list')

    def form_valid(self, form):
        messages.success(self.request, 'Type de réparation créé avec succès.')
        return super().form_valid(form)


class TypeReparationUpdateView(AdminRequiredMixin, UpdateView):
    """Modifier un type de réparation."""
    model = TypeReparation
    form_class = TypeReparationForm
    template_name = 'vehicules/type_reparation_form.html'
    success_url = reverse_lazy('vehicules:type_reparation_list')

    def form_valid(self, form):
        messages.success(self.request, 'Type de réparation modifié avec succès.')
        return super().form_valid(form)


class TypeReparationDeleteView(AdminRequiredMixin, DeleteView):
    """Supprimer un type de réparation."""
    model = TypeReparation
    template_name = 'vehicules/type_reparation_confirm_delete.html'
    success_url = reverse_lazy('vehicules:type_reparation_list')

    def form_valid(self, form):
        messages.success(self.request, 'Type de réparation supprimé avec succès.')
        return super().form_valid(form)



# ==================== API AJAX ====================

@require_http_methods(["GET"])
def get_types_reparation(request):
    """
    Vue AJAX pour récupérer la liste des types de réparation actifs.
    Utilisé par le modal de création de réparation depuis une dépense.
    """
    try:
        types = TypeReparation.objects.filter(actif=True).order_by('nom')
        
        types_data = [
            {
                'id': t.id,
                'nom': t.nom,
                'description': t.description or ''
            }
            for t in types
        ]
        
        return JsonResponse({
            'success': True,
            'types': types_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
