from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from core.mixins import AdminRequiredMixin

logger = logging.getLogger(__name__)
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
        queryset = super().get_queryset().annotate(nb_vehicules=Count('vehicules'))
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
        context['nb_total'] = ModeleVehicule.objects.count()
        context['nb_marques'] = ModeleVehicule.objects.values('marque').distinct().count()
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
        queryset = super().get_queryset().select_related('modele')
        search = self.request.GET.get('q', '')
        statut = self.request.GET.get('statut', 'tous')

        if search:
            queryset = queryset.filter(
                Q(immatriculation__icontains=search) |
                Q(modele__nom__icontains=search) |
                Q(modele__marque__icontains=search)
            )
        if statut == 'actif':
            queryset = queryset.filter(actif=True)
        elif statut == 'inactif':
            queryset = queryset.filter(actif=False)
        elif statut == 'en_reparation':
            queryset = queryset.filter(
                reparations__statut__in=['en_attente', 'en_cours']
            ).distinct()

        return queryset.order_by('-actif', 'immatriculation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_vehicules = Vehicule.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['statut_filtre'] = self.request.GET.get('statut', 'tous')
        context['nb_total'] = all_vehicules.count()
        context['nb_actifs'] = all_vehicules.filter(actif=True).count()
        context['nb_inactifs'] = all_vehicules.filter(actif=False).count()
        context['nb_en_reparation'] = all_vehicules.filter(
            reparations__statut__in=['en_attente', 'en_cours']
        ).distinct().count()
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
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()

        vehicule_id = self.request.GET.get('vehicule')
        if vehicule_id:
            queryset = queryset.filter(vehicule_id=vehicule_id)

        type_reparation = self.request.GET.get('type')
        if type_reparation:
            queryset = queryset.filter(type_reparation_id=type_reparation)

        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)

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

        all_reps = ReparationVehicule.objects.all()
        context['nb_total']    = all_reps.count()
        context['nb_attente']  = all_reps.filter(statut='en_attente').count()
        context['nb_en_cours'] = all_reps.filter(statut='en_cours').count()
        context['nb_termines'] = all_reps.filter(statut='terminee').count()

        queryset = self.get_queryset()
        context['cout_total_periode'] = queryset.aggregate(total=Sum('montant'))['total'] or 0

        context['vehicule_filtre']    = self.request.GET.get('vehicule', '')
        context['type_filtre']        = self.request.GET.get('type', '')
        context['statut_filtre']      = self.request.GET.get('statut', '')
        context['date_debut_filtre']  = self.request.GET.get('date_debut', '')
        context['date_fin_filtre']    = self.request.GET.get('date_fin', '')

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

    def dispatch(self, request, *args, **kwargs):
        reparation = get_object_or_404(ReparationVehicule, pk=kwargs['pk'])
        if reparation.statut == 'terminee':
            messages.error(request, "Cette réparation est terminée et ne peut plus être modifiée.")
            return redirect('vehicules:reparation_detail', pk=reparation.pk)
        return super().dispatch(request, *args, **kwargs)

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

    def dispatch(self, request, *args, **kwargs):
        reparation = get_object_or_404(ReparationVehicule, pk=kwargs['pk'])
        if reparation.statut == 'terminee':
            messages.error(request, "Cette réparation est terminée et ne peut pas être supprimée.")
            return redirect('vehicules:reparation_detail', pk=reparation.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Réparation supprimée avec succès.')
        return super().form_valid(form)


# Vue pour le rapport analytique
class RapportReparationsView(AdminRequiredMixin, TemplateView):
    """Rapport analytique des réparations véhicules."""
    template_name = 'vehicules/rapport_reparations.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
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
            for vehicule in Vehicule.objects.select_related('modele').all():
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
                {'label': t['label'], 'cout': float(t['cout']), 'pourcentage': float(round(t['pourcentage'], 1))}
                for t in types_stats
            ])

            # Véhicules critiques (> 2M)
            context['vehicules_critiques'] = [v for v in vehicules_stats if v['niveau_alerte'] == 'critique']

            # JSON pour le graphique véhicules
            context['vehicules_stats_json'] = json.dumps([
                {
                    'label': v['vehicule'].immatriculation,
                    'cout': float(v['cout_total']),
                    'niveau': v['niveau_alerte']
                }
                for v in vehicules_stats[:10]
            ])

            # Coût moyen par véhicule
            context['cout_moyen_vehicule'] = (
                int(context['cout_total'] / context['nb_vehicules'])
                if context['nb_vehicules'] > 0 else 0
            )

            # Matrice heatmap : véhicule × type de réparation
            types_actifs = TypeReparation.objects.filter(actif=True).order_by('nom')
            types_noms = [t.nom for t in types_actifs]
            context['types_actifs_noms'] = types_noms
            context['types_actifs_noms_json'] = json.dumps(types_noms)

            matrice = []
            for v_stat in vehicules_stats:
                vehicule = v_stat['vehicule']
                reps_veh = reparations.filter(vehicule=vehicule)
                costs = {}
                for type_rep in types_actifs:
                    montant = reps_veh.filter(type_reparation=type_rep).aggregate(
                        total=Sum('montant')
                    )['total'] or 0
                    costs[type_rep.nom] = float(montant)
                matrice.append({
                    'label': vehicule.immatriculation,
                    'costs': costs,
                    'total': float(v_stat['cout_total']),
                    'niveau': v_stat['niveau_alerte'],
                })
            context['matrice_json'] = json.dumps(matrice)

        except Exception as e:
            logger.error(f"Erreur dans RapportReparationsView: {e}", exc_info=True)
            context.setdefault('date_debut', datetime.now().strftime('%Y-%m-%d'))
            context.setdefault('date_fin', datetime.now().strftime('%Y-%m-%d'))
            context.setdefault('cout_total', 0)
            context.setdefault('nb_reparations', 0)
            context.setdefault('nb_vehicules', 0)
            context.setdefault('vehicules_stats', [])
            context.setdefault('types_stats', [])
            context.setdefault('types_stats_json', '[]')
            context.setdefault('vehicules_stats_json', '[]')
            context.setdefault('vehicules_critiques', [])
            context.setdefault('cout_moyen_vehicule', 0)
            context.setdefault('types_actifs_noms', [])
            context.setdefault('types_actifs_noms_json', '[]')
            context.setdefault('matrice_json', '[]')

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



# ==================== RENTABILITÉ VÉHICULE ====================

class RentabiliteVehiculeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Rapport de rentabilité d'un véhicule sur une période donnée."""
    template_name = 'vehicules/rentabilite.html'

    def test_func(self):
        """Accessible uniquement par PDG, Super Admin et Manager."""
        return self.request.user.role in ['pdg', 'super_admin', 'manager']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Paramètres de filtrage
        vehicule_id = self.request.GET.get('vehicule')
        date_debut_str = self.request.GET.get('date_debut')
        date_fin_str = self.request.GET.get('date_fin')

        today = timezone.now().date()

        # Parse des dates
        if date_debut_str:
            try:
                date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
            except ValueError:
                date_debut = today.replace(day=1)
        else:
            date_debut = today.replace(day=1)

        if date_fin_str:
            try:
                date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()
            except ValueError:
                date_fin = today
        else:
            date_fin = today

        if date_fin < date_debut:
            date_fin = date_debut

        context['date_debut'] = date_debut
        context['date_fin'] = date_fin

        # Liste des véhicules pour le filtre
        context['vehicules'] = Vehicule.objects.select_related('modele').order_by('immatriculation')

        # Véhicule sélectionné
        vehicule_selectionne = None
        if vehicule_id:
            try:
                vehicule_selectionne = Vehicule.objects.select_related('modele').get(id=vehicule_id)
            except Vehicule.DoesNotExist:
                pass
        context['vehicule_selectionne'] = vehicule_selectionne

        if not vehicule_selectionne:
            context['donnees_rapport'] = []
            return context

        # Voyages du véhicule sur la période
        from apps.voyages.models import Voyage
        voyages_query = Voyage.objects.filter(
            vehicule=vehicule_selectionne,
            date_depart__gte=date_debut,
            date_depart__lte=date_fin,
            statut__in=['programme', 'en_cours', 'termine']
        ).select_related('gare', 'ligne').prefetch_related(
            'billets', 'depenses', 'depenses__type_depense'
        ).order_by('date_depart', 'heure_depart', 'numero_depart')

        # Construire les données du rapport
        donnees_rapport = []
        types_depenses_presents = set()
        total_nb_passagers = 0
        total_recette_billets = Decimal('0')
        total_recette_bagages = Decimal('0')
        total_depenses = Decimal('0')

        for voyage in voyages_query:
            nb_passagers = voyage.billets.filter(statut='paye').count()
            recette_billets = voyage.billets.filter(statut='paye').aggregate(
                total=Sum('montant')
            )['total'] or Decimal('0')
            recette_bagages = voyage.recette_bagages or Decimal('0')

            # Dépenses par type
            depenses_par_type = {}
            total_depenses_voyage = Decimal('0')

            for depense in voyage.depenses.all():
                type_nom = depense.type_depense.nom
                if type_nom not in depenses_par_type:
                    depenses_par_type[type_nom] = Decimal('0')
                depenses_par_type[type_nom] += depense.montant
                total_depenses_voyage += depense.montant
                types_depenses_presents.add(type_nom)

            benefice_net = (recette_billets + recette_bagages) - total_depenses_voyage

            donnees_rapport.append({
                'voyage': voyage,
                'date': voyage.date_depart,
                'gare': voyage.gare.nom,
                'ligne': voyage.ligne.nom,
                'numero_depart': voyage.numero_depart,
                'nb_passagers': nb_passagers,
                'recette_billets': recette_billets,
                'recette_bagages': recette_bagages,
                'depenses': depenses_par_type,
                'total_depenses': total_depenses_voyage,
                'benefice_net': benefice_net,
            })

            total_nb_passagers += nb_passagers
            total_recette_billets += recette_billets
            total_recette_bagages += recette_bagages
            total_depenses += total_depenses_voyage

        context['donnees_rapport'] = donnees_rapport
        context['types_depenses_presents'] = sorted(list(types_depenses_presents))

        # Réparations du véhicule sur la période
        total_reparations = ReparationVehicule.objects.filter(
            vehicule=vehicule_selectionne,
            date_reparation__gte=date_debut,
            date_reparation__lte=date_fin
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')

        # Colonnes dynamiques
        colonnes = ['Date', 'Gare', 'Ligne', 'N° Départ', 'Nb Pass.', 'Recette Billets', 'Recette Bagages']
        colonnes.extend(sorted(list(types_depenses_presents)))
        colonnes.extend(['Total Dépenses', 'Bénéfice Net'])
        context['colonnes'] = colonnes

        # Totaux par colonne
        totaux = {
            'nb_passagers': total_nb_passagers,
            'recette_billets': total_recette_billets,
            'recette_bagages': total_recette_bagages,
            'total_depenses': total_depenses,
            'benefice_net': (total_recette_billets + total_recette_bagages) - total_depenses,
        }
        for type_dep_nom in types_depenses_presents:
            totaux[type_dep_nom] = sum(
                d['depenses'].get(type_dep_nom, Decimal('0'))
                for d in donnees_rapport
            )
        context['totaux'] = totaux

        # Cartes récapitulatives
        context['nb_voyages'] = len(donnees_rapport)
        context['total_recette_billets'] = total_recette_billets
        context['total_recette_bagages'] = total_recette_bagages
        context['total_depenses'] = total_depenses
        context['total_reparations'] = total_reparations
        context['benefice_net_global'] = (total_recette_billets + total_recette_bagages) - total_depenses - total_reparations

        return context


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
