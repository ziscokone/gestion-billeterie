from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal, InvalidOperation
from datetime import timedelta
from core.mixins import GestionRequiredMixin
from .models import Voyage
from .forms import VoyageForm
from apps.compagnie.models import Compagnie
from apps.personnel.models import Chauffeur, Convoyeur
from apps.comptabilite.models import TypeDepense, Depense
from apps.vehicules.models import Vehicule
from apps.billets.models import Billet, HistoriqueReport


class VoyageListView(GestionRequiredMixin, ListView):
    """Liste des voyages."""
    model = Voyage
    template_name = 'voyages/voyage_list.html'
    context_object_name = 'voyages'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filtrer par gare pour les chefs de gare et guichetiers
        if not user.has_global_access and user.gare:
            queryset = queryset.filter(gare=user.gare)

        # Filtre par date (par défaut les 7 prochains jours)
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')

        if not date_debut:
            date_debut = timezone.now().date()
        else:
            from datetime import datetime
            date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()

        if not date_fin:
            date_fin = date_debut + timedelta(days=7)
        else:
            from datetime import datetime
            date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()

        queryset = queryset.filter(
            date_depart__gte=date_debut,
            date_depart__lte=date_fin
        )

        # Recherche
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(ligne__nom__icontains=search) |
                Q(ligne__ville_arrivee__icontains=search) |
                Q(vehicule__immatriculation__icontains=search)
            )

        # Filtre par statut
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)

        return queryset.select_related(
            'gare', 'ligne', 'vehicule', 'chauffeur', 'convoyeur'
        ).annotate(
            nb_billets=Count('billets')
        ).order_by('date_depart', 'heure_depart')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['date_debut'] = self.request.GET.get('date_debut', timezone.now().date().isoformat())
        context['date_fin'] = self.request.GET.get('date_fin', (timezone.now().date() + timedelta(days=7)).isoformat())
        context['statut_filtre'] = self.request.GET.get('statut', '')
        context['statut_choices'] = Voyage.STATUT_CHOICES
        return context


class VoyageDetailView(GestionRequiredMixin, DetailView):
    """Détail d'un voyage avec la grille des sièges."""
    model = Voyage
    template_name = 'voyages/voyage_detail.html'
    context_object_name = 'voyage'

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filtrer par gare pour les chefs de gare et guichetiers
        if not user.has_global_access and user.gare:
            queryset = queryset.filter(gare=user.gare)

        return queryset.select_related(
            'gare', 'ligne', 'vehicule', 'vehicule__modele',
            'chauffeur', 'convoyeur'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voyage = self.object

        # Récupérer tous les billets du voyage
        billets = voyage.billets.select_related('guichetier').order_by('numero_siege')
        billets_payes = billets.filter(statut='paye')

        context['billets'] = billets
        context['billets_payes'] = billets_payes
        context['billets_reserves'] = billets.filter(statut='reserve')

        # Calculer les statistiques
        context['nb_billets_payes'] = billets_payes.count()
        context['nb_billets_reserves'] = billets.filter(statut='reserve').count()
        context['montant_total'] = sum(b.montant for b in billets_payes)

        # Statistiques par moyen de paiement (uniquement billets payés)
        context['paiements_cash'] = billets_payes.filter(moyen_paiement='cash').count()
        context['paiements_wave'] = billets_payes.filter(moyen_paiement='wave').count()
        context['paiements_orange'] = billets_payes.filter(moyen_paiement='orange_money').count()
        context['paiements_mtn'] = billets_payes.filter(moyen_paiement='mtn_money').count()
        context['paiements_moov'] = billets_payes.filter(moyen_paiement='moov_money').count()

        return context


class VoyageCreateView(GestionRequiredMixin, CreateView):
    """Créer un nouveau voyage manuellement."""
    model = Voyage
    form_class = VoyageForm
    template_name = 'voyages/voyage_form.html'
    success_url = reverse_lazy('voyages:voyage_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Voyage créé avec succès.')
        return super().form_valid(form)


class VoyageUpdateView(GestionRequiredMixin, UpdateView):
    """Modifier un voyage."""
    model = Voyage
    form_class = VoyageForm
    template_name = 'voyages/voyage_form.html'
    success_url = reverse_lazy('voyages:voyage_list')

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filtrer par gare pour les chefs de gare et guichetiers
        if not user.has_global_access and user.gare:
            queryset = queryset.filter(gare=user.gare)

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Voyage modifié avec succès.')
        return super().form_valid(form)


class VoyageDeleteView(GestionRequiredMixin, DeleteView):
    """Supprimer un voyage."""
    model = Voyage
    template_name = 'voyages/voyage_confirm_delete.html'
    success_url = reverse_lazy('voyages:voyage_list')

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filtrer par gare pour les chefs de gare et guichetiers
        if not user.has_global_access and user.gare:
            queryset = queryset.filter(gare=user.gare)

        return queryset

    def form_valid(self, form):
        messages.success(self.request, 'Voyage supprimé avec succès.')
        return super().form_valid(form)


class VoyageBordereauView(GestionRequiredMixin, TemplateView):
    """Vue pour le bordereau d'impression du voyage."""
    template_name = 'voyages/voyage_bordereau.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voyage_id = self.kwargs.get('pk')
        voyage = get_object_or_404(
            Voyage.objects.select_related(
                'gare', 'ligne', 'vehicule', 'vehicule__modele'
            ),
            pk=voyage_id
        )

        # Vérifier les permissions
        user = self.request.user
        if not user.has_global_access and user.gare:
            if voyage.gare != user.gare:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Accès non autorisé")

        # Récupérer uniquement les billets payés (exclure réservés et reportés)
        billets = voyage.billets.filter(statut='paye').select_related('guichetier').order_by('numero_siege')

        # Récupérer les dépenses du voyage
        depenses = voyage.depenses.select_related('type_depense').order_by('type_depense__ordre', 'type_depense__nom')
        total_depenses = sum((d.montant for d in depenses), Decimal('0'))

        # Calculer les totaux
        montant_total_billets = sum(b.montant for b in billets)
        recette_bagages = voyage.recette_bagages or Decimal('0')
        total_recettes = voyage.get_total_recettes()
        benefice_net = voyage.get_benefice_net()

        context['voyage'] = voyage
        context['billets'] = billets
        context['billets_payes'] = billets
        context['nb_billets_payes'] = billets.count()
        context['nb_billets_reserves'] = 0  # Non affichés sur le bordereau
        context['montant_total'] = montant_total_billets
        context['recette_bagages'] = recette_bagages
        context['total_recettes'] = total_recettes
        context['depenses'] = depenses
        context['total_depenses'] = total_depenses
        context['benefice_net'] = benefice_net
        context['compagnie'] = Compagnie.get_instance()
        context['print_mode'] = self.request.GET.get('print', '0') == '1'
        context['date_impression'] = timezone.now()

        return context


class VoyageListePassagersView(GestionRequiredMixin, TemplateView):
    """Vue pour la liste des passagers du voyage."""
    template_name = 'voyages/liste_passagers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voyage_id = self.kwargs.get('pk')
        voyage = get_object_or_404(
            Voyage.objects.select_related(
                'gare', 'ligne', 'vehicule', 'vehicule__modele'
            ),
            pk=voyage_id
        )

        # Vérifier les permissions
        user = self.request.user
        if not user.has_global_access and user.gare:
            if voyage.gare != user.gare:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Accès non autorisé")

        # Récupérer uniquement les billets payés (exclure réservés et reportés)
        billets = voyage.billets.filter(statut='paye').select_related('destination', 'guichetier').order_by('numero_siege')

        context['voyage'] = voyage
        context['billets'] = billets
        context['compagnie'] = Compagnie.get_instance()
        context['print_mode'] = self.request.GET.get('print', '0') == '1'
        context['date_impression'] = timezone.now()

        return context


class VoyageRecapDestinationView(GestionRequiredMixin, TemplateView):
    """Vue pour le récapitulatif des destinations (format ticket 80x80mm)."""
    template_name = 'voyages/voyage_recap_destination.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voyage_id = self.kwargs.get('pk')
        voyage = get_object_or_404(
            Voyage.objects.select_related(
                'gare', 'ligne', 'vehicule', 'vehicule__modele'
            ),
            pk=voyage_id
        )

        # Vérifier les permissions
        user = self.request.user
        if not user.has_global_access and user.gare:
            if voyage.gare != user.gare:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Accès non autorisé")

        # Récupérer uniquement les billets payés (exclure réservés et reportés)
        billets = voyage.billets.filter(statut='paye').select_related('destination').all()

        # Compter les passagers par destination (ordre alphabétique)
        destinations_count = {}
        for billet in billets:
            if billet.destination:
                ville = billet.destination.ville_arrivee
            else:
                ville = voyage.ligne.ville_arrivee

            if ville in destinations_count:
                destinations_count[ville] += 1
            else:
                destinations_count[ville] = 1

        # Trier par ordre alphabétique
        destinations_sorted = sorted(destinations_count.items(), key=lambda x: x[0])

        context['voyage'] = voyage
        context['destinations'] = destinations_sorted
        context['total_passagers'] = sum(count for _, count in destinations_sorted)
        context['compagnie'] = Compagnie.get_instance()
        context['print_mode'] = self.request.GET.get('print', '0') == '1'
        context['date_impression'] = timezone.now()

        return context


@require_http_methods(["GET"])
def get_voyage_agents(request, pk):
    """
    Vue AJAX pour récupérer la liste des chauffeurs et convoyeurs actifs.
    Retourne également les agents actuellement assignés au voyage.
    """
    try:
        # Récupérer le voyage
        voyage = get_object_or_404(Voyage, pk=pk)

        # Vérifier les permissions
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        if not user.has_global_access and user.gare:
            if voyage.gare != user.gare:
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

        # Récupérer tous les chauffeurs actifs
        chauffeurs = Chauffeur.objects.filter(actif=True).order_by('nom_complet')
        chauffeurs_data = [
            {'id': c.id, 'nom_complet': c.nom_complet}
            for c in chauffeurs
        ]

        # Récupérer tous les convoyeurs actifs
        convoyeurs = Convoyeur.objects.filter(actif=True).order_by('nom_complet')
        convoyeurs_data = [
            {'id': c.id, 'nom_complet': c.nom_complet}
            for c in convoyeurs
        ]

        # Calculer le plus haut numéro de siège vendu pour filtrer les véhicules
        max_siege = voyage.billets.aggregate(max_siege=Max('numero_siege'))['max_siege']
        capacite_minimale = max_siege if max_siege else 0

        # Récupérer tous les véhicules actifs avec capacité suffisante
        # Exclure les véhicules en réparation (statut en_attente ou en_cours)
        vehicules = Vehicule.objects.filter(
            actif=True,
            modele__capacite__gte=capacite_minimale
        ).exclude(
            reparations__statut__in=['en_attente', 'en_cours']
        ).select_related('modele', 'compagnie').order_by('immatriculation')

        vehicules_data = [
            {
                'id': v.id,
                'immatriculation': v.immatriculation,
                'modele_nom': v.modele.nom,
                'capacite': v.capacite
            }
            for v in vehicules
        ]

        # Informations du voyage
        voyage_data = {
            'chauffeur_id': voyage.chauffeur.id if voyage.chauffeur else None,
            'convoyeur_id': voyage.convoyeur.id if voyage.convoyeur else None,
            'vehicule_id': voyage.vehicule.id if voyage.vehicule else None,
        }

        return JsonResponse({
            'success': True,
            'chauffeurs': chauffeurs_data,
            'convoyeurs': convoyeurs_data,
            'vehicules': vehicules_data,
            'capacite_minimale': capacite_minimale,
            'voyage': voyage_data
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def save_voyage_agents(request, pk):
    """
    Vue AJAX pour enregistrer les agents (chauffeur et convoyeur) d'un voyage.
    Sauvegarde permanente en base de données.
    """
    try:
        # Récupérer le voyage
        voyage = get_object_or_404(Voyage, pk=pk)

        # Vérifier les permissions
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        if not user.has_global_access and user.gare:
            if voyage.gare != user.gare:
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

        # Récupérer les données JSON
        data = json.loads(request.body)
        chauffeur_id = data.get('chauffeur_id')
        convoyeur_id = data.get('convoyeur_id')
        vehicule_id = data.get('vehicule_id')

        # Assigner le chauffeur
        if chauffeur_id:
            chauffeur = get_object_or_404(Chauffeur, pk=chauffeur_id, actif=True)
            voyage.chauffeur = chauffeur
        else:
            voyage.chauffeur = None

        # Assigner le convoyeur
        if convoyeur_id:
            convoyeur = get_object_or_404(Convoyeur, pk=convoyeur_id, actif=True)
            voyage.convoyeur = convoyeur
        else:
            voyage.convoyeur = None

        # Assigner le véhicule
        if vehicule_id:
            # Vérifier que le véhicule existe et est actif
            vehicule = get_object_or_404(Vehicule, pk=vehicule_id, actif=True)

            # Vérification : véhicule pas en réparation
            if vehicule.est_en_reparation:
                return JsonResponse({
                    'success': False,
                    'error': f'Le véhicule {vehicule.immatriculation} est actuellement en réparation '
                             f'et ne peut pas être assigné à un voyage.'
                }, status=400)

            # Vérification supplémentaire : capacité suffisante
            max_siege = voyage.billets.aggregate(max_siege=Max('numero_siege'))['max_siege']
            if max_siege and vehicule.capacite < max_siege:
                return JsonResponse({
                    'success': False,
                    'error': f'Le véhicule sélectionné a une capacité de {vehicule.capacite} places, '
                             f'mais le siège {max_siege} a déjà été vendu.'
                }, status=400)

            voyage.vehicule = vehicule
        else:
            voyage.vehicule = None

        # Sauvegarder en base de données
        voyage.save(update_fields=['chauffeur', 'convoyeur', 'vehicule', 'date_modification'])

        return JsonResponse({
            'success': True,
            'message': 'Agents et véhicule enregistrés avec succès',
            'chauffeur_nom': voyage.chauffeur.nom_complet if voyage.chauffeur else None,
            'convoyeur_nom': voyage.convoyeur.nom_complet if voyage.convoyeur else None,
            'vehicule_immatriculation': voyage.vehicule.immatriculation if voyage.vehicule else None,
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== GESTION DES DÉPENSES DU VOYAGE ==========

@require_http_methods(["GET"])
def get_voyage_depenses(request, pk):
    """
    Vue AJAX pour récupérer les types de dépenses actifs et les dépenses du voyage.
    """
    try:
        # Récupérer le voyage
        voyage = get_object_or_404(Voyage, pk=pk)

        # Vérifier les permissions
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        if not user.has_global_access and user.gare:
            if voyage.gare != user.gare:
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

        # Récupérer la compagnie du voyage
        compagnie = voyage.gare.compagnie if hasattr(voyage.gare, 'compagnie') else None
        if not compagnie:
            # Fallback: récupérer via la compagnie singleton
            compagnie = Compagnie.get_instance()

        # Récupérer tous les types de dépenses actifs de la compagnie
        types_depenses = TypeDepense.objects.filter(
            compagnie=compagnie,
            actif=True
        ).order_by('ordre', 'nom')

        types_data = [
            {
                'id': t.id,
                'code': t.code,
                'nom': t.nom,
                'description_obligatoire': t.description_obligatoire,
                'ordre': t.ordre
            }
            for t in types_depenses
        ]

        # Récupérer toutes les dépenses du voyage
        depenses = voyage.depenses.select_related('type_depense', 'guichetier').order_by('-date_creation')

        depenses_data = [
            {
                'id': d.id,
                'type_depense_id': d.type_depense.id,
                'type_depense_code': d.type_depense.code,
                'type_depense_nom': d.type_depense.nom,
                'montant': float(d.montant),
                'description': d.description or '',
                'guichetier': d.guichetier.nom_complet if d.guichetier else 'Inconnu',
                'date_creation': d.date_creation.strftime('%d/%m/%Y %H:%M'),
                'reparation_id': d.reparation.id if d.reparation else None,
                'peut_creer_reparation': d.peut_creer_reparation()
            }
            for d in depenses
        ]

        # Calculer le total des dépenses
        total_depenses = sum((d.montant for d in depenses), Decimal('0'))

        return JsonResponse({
            'success': True,
            'types_depenses': types_data,
            'depenses': depenses_data,
            'total_depenses': float(total_depenses)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def add_voyage_depenses(request, pk):
    """
    Vue AJAX pour ajouter une ou plusieurs dépenses à un voyage.
    """
    try:
        # Récupérer le voyage
        voyage = get_object_or_404(Voyage, pk=pk)

        # Vérifier les permissions
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        if not user.has_global_access and user.gare:
            if voyage.gare != user.gare:
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

        # Récupérer les données JSON
        data = json.loads(request.body)
        depenses_list = data.get('depenses', [])

        if not depenses_list:
            return JsonResponse({'success': False, 'error': 'Aucune dépense à enregistrer'}, status=400)

        depenses_creees = []
        erreurs = []

        for depense_data in depenses_list:
            type_depense_id = depense_data.get('type_depense_id')
            montant = depense_data.get('montant')
            description = depense_data.get('description', '').strip()

            # Validation
            if not type_depense_id:
                erreurs.append("Type de dépense manquant")
                continue

            if not montant or float(montant) <= 0:
                continue  # Ignorer les montants vides ou nuls

            # Récupérer le type de dépense
            try:
                type_depense = TypeDepense.objects.get(pk=type_depense_id, actif=True)
            except TypeDepense.DoesNotExist:
                erreurs.append(f"Type de dépense invalide: {type_depense_id}")
                continue

            # Vérifier si la description est obligatoire
            if type_depense.description_obligatoire and not description:
                erreurs.append(f"La description est obligatoire pour '{type_depense.nom}'")
                continue

            # Créer la dépense
            depense = Depense(
                voyage=voyage,
                type_depense=type_depense,
                montant=float(montant),
                description=description,
                guichetier=user
            )

            try:
                depense.save()
                depenses_creees.append({
                    'id': depense.id,
                    'type_depense_nom': depense.type_depense.nom,
                    'montant': float(depense.montant),
                    'description': depense.description
                })
            except Exception as e:
                erreurs.append(f"Erreur lors de l'enregistrement: {str(e)}")

        # Calculer le nouveau total
        total_depenses = sum((d.montant for d in voyage.depenses.all()), Decimal('0'))

        if erreurs:
            return JsonResponse({
                'success': False,
                'error': '; '.join(erreurs),
                'depenses_creees': depenses_creees,
                'total_depenses': float(total_depenses)
            }, status=400)

        return JsonResponse({
            'success': True,
            'message': f'{len(depenses_creees)} dépense(s) enregistrée(s) avec succès',
            'depenses_creees': depenses_creees,
            'total_depenses': float(total_depenses)
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== GESTION DE LA RECETTE BAGAGES ====================

@require_http_methods(["GET"])
def get_voyage_bagages(request, pk):
    """
    Récupère la recette bagages d'un voyage.
    """
    voyage = get_object_or_404(Voyage, pk=pk)
    user = request.user

    # Vérification du rôle - Seuls Super Admin, PDG, Manager et Chef de Gare peuvent accéder
    if not (user.is_super_admin or user.is_pdg or user.is_manager or user.is_chef_gare):
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'avez pas les permissions pour accéder à cette fonctionnalité'
        }, status=403)

    # Vérification des permissions de gare
    if not user.has_global_access and voyage.gare != user.gare:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'avez pas accès à ce voyage'
        }, status=403)

    return JsonResponse({
        'success': True,
        'recette_bagages': float(voyage.recette_bagages or 0)
    })


@require_http_methods(["POST"])
def save_voyage_bagages(request, pk):
    """
    Enregistre la recette bagages d'un voyage.
    """
    voyage = get_object_or_404(Voyage, pk=pk)
    user = request.user

    # Vérification du rôle - Seuls Super Admin, PDG, Manager et Chef de Gare peuvent modifier
    if not (user.is_super_admin or user.is_pdg or user.is_manager or user.is_chef_gare):
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'avez pas les permissions pour modifier la recette bagages'
        }, status=403)

    # Vérification des permissions de gare
    if not user.has_global_access and voyage.gare != user.gare:
        return JsonResponse({
            'success': False,
            'error': 'Vous n\'avez pas accès à ce voyage'
        }, status=403)

    try:
        data = json.loads(request.body)
        montant = data.get('montant', 0)

        # Validation du montant
        try:
            montant = Decimal(str(montant))
            if montant < 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Le montant ne peut pas être négatif'
                }, status=400)
        except (ValueError, TypeError, InvalidOperation):
            return JsonResponse({
                'success': False,
                'error': 'Montant invalide'
            }, status=400)

        # Enregistrer la recette bagages
        voyage.recette_bagages = montant
        voyage.save(update_fields=['recette_bagages', 'date_modification'])

        # Calculer les totaux pour la réponse
        total_billets = voyage.get_montant_total()
        total_recettes = voyage.get_total_recettes()
        total_depenses = sum((d.montant for d in voyage.depenses.all()), Decimal('0'))
        benefice_net = voyage.get_benefice_net()

        return JsonResponse({
            'success': True,
            'message': 'Recette bagages enregistrée avec succès',
            'recette_bagages': float(voyage.recette_bagages),
            'total_billets': float(total_billets),
            'total_recettes': float(total_recettes),
            'total_depenses': float(total_depenses),
            'benefice_net': float(benefice_net)
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== GESTION DU STATUT DU VOYAGE ====================

@require_http_methods(["POST"])
def terminer_voyage(request, pk):
    """
    Termine un voyage (change le statut de 'programme' ou 'en_cours' à 'termine').
    Accessible à tous les guichetiers de la gare.
    """
    try:
        # Récupérer le voyage
        voyage = get_object_or_404(Voyage, pk=pk)

        # Vérifier l'authentification
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        # Vérifier les permissions de gare
        if not user.has_global_access and user.gare:
            if voyage.gare != user.gare:
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

        # Vérifier que le statut actuel permet la terminaison
        if voyage.statut not in ['programme', 'en_cours']:
            return JsonResponse({
                'success': False,
                'error': f'Impossible de terminer un voyage avec le statut "{voyage.get_statut_display()}"'
            }, status=400)

        # Changer le statut à 'termine'
        voyage.statut = 'termine'
        voyage.save(update_fields=['statut', 'date_modification'])

        return JsonResponse({
            'success': True,
            'message': 'Le départ a été marqué comme terminé avec succès',
            'nouveau_statut': voyage.get_statut_display()
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==================== GESTION DU REPORT DE BILLETS ====================

@require_http_methods(["GET"])
def get_voyages_report(request, billet_id):
    """
    Vue AJAX pour récupérer la liste des voyages disponibles pour le report d'un billet.
    Retourne les voyages à venir de la même ligne, groupés par date.
    """
    try:
        # Récupérer le billet
        billet = get_object_or_404(Billet, pk=billet_id)
        voyage_actuel = billet.voyage

        # Vérifier les permissions
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        if not user.has_global_access and user.gare:
            if voyage_actuel.gare != user.gare:
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

        # Récupérer les voyages à venir de la même ligne (exclure le voyage actuel)
        date_aujourdhui = timezone.now().date()
        voyages_disponibles = Voyage.objects.filter(
            gare=voyage_actuel.gare,
            ligne=voyage_actuel.ligne,
            date_depart__gte=date_aujourdhui,
            statut__in=['programme', 'en_cours']
        ).exclude(
            pk=voyage_actuel.pk  # Exclure le voyage actuel
        ).select_related(
            'vehicule', 'vehicule__modele'
        ).order_by('date_depart', 'heure_depart')

        # Grouper les voyages par date
        voyages_groupes = {}
        for voyage in voyages_disponibles:
            date_str = voyage.date_depart.strftime('%Y-%m-%d')
            date_display = voyage.date_depart.strftime('%d/%m/%Y')

            # Déterminer le label du groupe
            if voyage.date_depart == date_aujourdhui:
                groupe_label = f"Aujourd'hui ({date_display})"
            elif voyage.date_depart == date_aujourdhui + timedelta(days=1):
                groupe_label = f"Demain ({date_display})"
            else:
                groupe_label = date_display

            if groupe_label not in voyages_groupes:
                voyages_groupes[groupe_label] = []

            # Calculer les places libres
            places_libres = len(voyage.get_sieges_disponibles())

            voyages_groupes[groupe_label].append({
                'id': voyage.id,
                'heure_depart': voyage.heure_depart.strftime('%H:%M'),
                'periode': voyage.get_periode_display(),
                'numero_depart': voyage.numero_depart,
                'places_libres': places_libres,
                'capacite': voyage.capacite,
                'vehicule': voyage.vehicule.immatriculation if voyage.vehicule else 'Non assigné'
            })

        return JsonResponse({
            'success': True,
            'voyages': voyages_groupes,
            'billet': {
                'numero': billet.numero,
                'client_nom': billet.client_nom,
                'client_telephone': billet.client_telephone,
                'siege_actuel': billet.numero_siege,
                'montant': float(billet.montant)
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_disposition_voyage(request, voyage_id):
    """
    Vue AJAX pour récupérer la disposition des sièges d'un voyage.
    """
    try:
        # Récupérer le voyage
        voyage = get_object_or_404(Voyage, pk=voyage_id)

        # Vérifier les permissions
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        if not user.has_global_access and user.gare:
            if voyage.gare != user.gare:
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

        # Vérifier si le voyage a un véhicule assigné
        if not voyage.vehicule:
            return JsonResponse({
                'success': False,
                'error': 'Ce voyage n\'a pas de véhicule assigné'
            }, status=400)

        # Récupérer la disposition brute du modèle de véhicule
        disposition_base = voyage.vehicule.modele.get_disposition_pour_affichage()

        # Récupérer les sièges occupés (excluant les reportés)
        sieges_occupes = list(
            voyage.billets.exclude(statut='reporte').values_list('numero_siege', flat=True)
        )

        # Enrichir la disposition avec le statut des sièges
        disposition_enrichie = {
            'colonnes': disposition_base.get('colonnes', 5),
            'rangees': []
        }

        for rangee in disposition_base.get('rangees', []):
            sieges_rangee = []
            for siege in rangee.get('sieges', []):
                if siege.get('type') == 'couloir' or siege.get('numero') is None:
                    # Couloir (None)
                    sieges_rangee.append(None)
                elif siege.get('type') == 'non_vendable':
                    # Siège non vendable
                    sieges_rangee.append({
                        'numero': siege['numero'],
                        'statut': 'non_vendable'
                    })
                else:
                    # Siège vendable - vérifier s'il est occupé
                    numero_siege = siege['numero']
                    if numero_siege in sieges_occupes:
                        sieges_rangee.append({
                            'numero': numero_siege,
                            'statut': 'occupe'
                        })
                    else:
                        sieges_rangee.append({
                            'numero': numero_siege,
                            'statut': 'disponible'
                        })

            disposition_enrichie['rangees'].append({
                'rang': rangee.get('rang'),
                'sieges': sieges_rangee
            })

        return JsonResponse({
            'success': True,
            'disposition': disposition_enrichie,
            'capacite': voyage.capacite,
            'places_libres': len(voyage.get_sieges_disponibles())
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def reporter_billet(request, billet_id):
    """
    Vue AJAX pour reporter un billet vers un autre voyage.
    """
    try:
        # Récupérer le billet
        ancien_billet = get_object_or_404(Billet, pk=billet_id)
        voyage_actuel = ancien_billet.voyage

        # Vérifier les permissions
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        if not user.has_global_access and user.gare:
            if voyage_actuel.gare != user.gare:
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

        # Récupérer les données JSON
        data = json.loads(request.body)
        nouveau_voyage_id = data.get('nouveau_voyage_id')
        nouveau_siege = data.get('nouveau_siege')
        motif = data.get('motif', '')

        # Validation
        if not nouveau_voyage_id:
            return JsonResponse({'success': False, 'error': 'Le nouveau voyage doit être spécifié'}, status=400)

        if not nouveau_siege:
            return JsonResponse({'success': False, 'error': 'Le nouveau siège doit être spécifié'}, status=400)

        if not motif:
            return JsonResponse({'success': False, 'error': 'Le motif du report doit être spécifié'}, status=400)

        # Vérifier que le billet n'a pas déjà été reporté
        if ancien_billet.statut == 'reporte':
            return JsonResponse({
                'success': False,
                'error': 'Ce billet a déjà été reporté'
            }, status=400)

        # Récupérer le nouveau voyage
        nouveau_voyage = get_object_or_404(Voyage, pk=nouveau_voyage_id)

        # Vérifier que le voyage est de la même gare et ligne
        if nouveau_voyage.gare != voyage_actuel.gare:
            return JsonResponse({
                'success': False,
                'error': 'Le nouveau voyage doit être de la même gare'
            }, status=400)

        if nouveau_voyage.ligne != voyage_actuel.ligne:
            return JsonResponse({
                'success': False,
                'error': 'Le nouveau voyage doit être de la même ligne'
            }, status=400)

        # Vérifier que le siège est disponible
        if not nouveau_voyage.siege_disponible(nouveau_siege):
            return JsonResponse({
                'success': False,
                'error': f'Le siège {nouveau_siege} n\'est pas disponible sur le nouveau voyage'
            }, status=400)

        # 1. Sauvegarder le montant de l'ancien billet avant modification
        montant_a_transferer = ancien_billet.montant

        # 2. Créer le NOUVEAU billet (le montant est transféré de l'ancien billet)
        numero_nouveau_billet = voyage_actuel.gare.generer_numero_ticket()
        nouveau_billet = Billet.objects.create(
            numero=numero_nouveau_billet,
            voyage=nouveau_voyage,
            destination=ancien_billet.destination,
            client_nom=ancien_billet.client_nom,
            client_telephone=ancien_billet.client_telephone,
            numero_siege=nouveau_siege,
            montant=montant_a_transferer,  # Le montant suit le client
            statut='paye',
            moyen_paiement=ancien_billet.moyen_paiement,
            guichetier=user,
            date_paiement=timezone.now()
        )

        # 3. Modifier l'ANCIEN billet (statut = reporté, montant = 0 pour libérer la place)
        ancien_billet.statut = 'reporte'
        ancien_billet.montant = 0  # Place libérée, peut être revendue
        ancien_billet.reporte_vers_billet = nouveau_billet
        ancien_billet.date_report = timezone.now()
        ancien_billet.guichetier_report = user
        ancien_billet.motif_report = motif
        ancien_billet.save(update_fields=['statut', 'montant', 'reporte_vers_billet', 'date_report', 'guichetier_report', 'motif_report', 'date_modification'])

        # 3. Créer l'historique de report
        HistoriqueReport.objects.create(
            ancien_billet=ancien_billet,
            nouveau_billet=nouveau_billet,
            ancien_voyage=voyage_actuel,
            nouveau_voyage=nouveau_voyage,
            ancien_siege=ancien_billet.numero_siege,
            nouveau_siege=nouveau_siege,
            guichetier=user,
            motif=motif
        )

        return JsonResponse({
            'success': True,
            'message': f'Billet reporté avec succès. Nouveau billet: {nouveau_billet.numero}',
            'ancien_billet': ancien_billet.numero,
            'nouveau_billet': nouveau_billet.numero,
            'nouveau_voyage': f"{nouveau_voyage.date_depart.strftime('%d/%m/%Y')} - {nouveau_voyage.heure_depart.strftime('%H:%M')}",
            'nouveau_siege': nouveau_siege
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def creer_reparation_depuis_depense(request, depense_id):
    """
    Vue AJAX pour créer une réparation depuis une dépense de voyage.
    Permet au guichetier de créer une fiche de réparation avec des infos minimales.
    """
    try:
        # Récupérer la dépense
        depense = get_object_or_404(Depense, pk=depense_id)
        voyage = depense.voyage

        # Vérifier les permissions
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Non authentifié'}, status=401)

        if not user.has_global_access and user.gare:
            if voyage.gare != user.gare:
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

        # Vérifier que c'est une dépense de type "Réparation" (par code OU par nom)
        is_reparation_type = (
            depense.type_depense.code == 'reparation' or
            'réparation' in depense.type_depense.nom.lower() or
            'reparation' in depense.type_depense.nom.lower()
        )
        if not is_reparation_type:
            return JsonResponse({
                'success': False,
                'error': 'Cette dépense n\'est pas de type "Réparation"'
            }, status=400)

        # Vérifier qu'elle n'a pas déjà une réparation liée
        if depense.a_reparation_liee():
            return JsonResponse({
                'success': False,
                'error': 'Une réparation a déjà été créée pour cette dépense'
            }, status=400)

        # Vérifier que le voyage a un véhicule assigné
        if not voyage.vehicule:
            return JsonResponse({
                'success': False,
                'error': 'Le voyage n\'a pas de véhicule assigné. Impossible de créer une réparation.'
            }, status=400)

        # Récupérer les données JSON
        data = json.loads(request.body)

        vehicule_id = data.get('vehicule_id')
        date_reparation = data.get('date_reparation')
        type_reparation_id = data.get('type_reparation_id')
        garage_prestataire = data.get('garage_prestataire', '').strip()
        description = data.get('description', '').strip()

        # Validation des champs obligatoires
        if not vehicule_id:
            return JsonResponse({'success': False, 'error': 'Le véhicule est obligatoire'}, status=400)

        if not date_reparation:
            return JsonResponse({'success': False, 'error': 'La date de réparation est obligatoire'}, status=400)

        if not type_reparation_id:
            return JsonResponse({'success': False, 'error': 'Le type de réparation est obligatoire'}, status=400)

        if not garage_prestataire:
            return JsonResponse({'success': False, 'error': 'Le garage/prestataire est obligatoire'}, status=400)

        # Récupérer le véhicule et le type de réparation
        from apps.vehicules.models import Vehicule, TypeReparation, ReparationVehicule
        from datetime import datetime

        try:
            vehicule = Vehicule.objects.get(pk=vehicule_id, actif=True)
        except Vehicule.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Véhicule invalide'}, status=400)

        try:
            type_reparation = TypeReparation.objects.get(pk=type_reparation_id, actif=True)
        except TypeReparation.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Type de réparation invalide'}, status=400)

        # Convertir la date
        try:
            date_reparation_obj = datetime.strptime(date_reparation, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Format de date invalide'}, status=400)

        # Créer la réparation
        reparation = ReparationVehicule.objects.create(
            vehicule=vehicule,
            date_reparation=date_reparation_obj,
            type_reparation=type_reparation,
            description=description or depense.description,
            garage_prestataire=garage_prestataire,
            montant=depense.montant,  # Montant de la dépense
            statut='en_attente',  # Statut automatique
            creee_depuis_guichet=True,
            voyage_source=voyage
        )

        # Lier la réparation à la dépense
        depense.reparation = reparation
        depense.save(update_fields=['reparation', 'date_modification'])

        return JsonResponse({
            'success': True,
            'message': f'Réparation créée avec succès (Fiche #{reparation.pk})',
            'reparation_id': reparation.pk,
            'reparation_numero': f"#{reparation.pk}",
            'vehicule': vehicule.immatriculation,
            'type_reparation': type_reparation.nom,
            'montant': float(reparation.montant)
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


class DashboardReportsView(GestionRequiredMixin, TemplateView):
    """Vue pour le dashboard des reports de billets."""
    template_name = 'voyages/dashboard_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filtres
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        guichetier_id = self.request.GET.get('guichetier')
        gare_id = self.request.GET.get('gare')

        # Query de base
        reports = HistoriqueReport.objects.select_related(
            'ancien_billet',
            'nouveau_billet',
            'ancien_voyage',
            'nouveau_voyage',
            'ancien_voyage__gare',
            'guichetier'
        )

        # Filtrer par gare si l'utilisateur n'a pas l'accès global
        if not self.request.user.has_global_access and self.request.user.gare:
            reports = reports.filter(ancien_voyage__gare=self.request.user.gare)
        # Pour les utilisateurs avec accès global, appliquer le filtre par gare si spécifié
        elif self.request.user.has_global_access and gare_id:
            reports = reports.filter(ancien_voyage__gare_id=gare_id)

        # Appliquer les filtres de date
        if date_debut:
            reports = reports.filter(date_report__date__gte=date_debut)
        if date_fin:
            reports = reports.filter(date_report__date__lte=date_fin)

        # Filtrer par guichetier
        if guichetier_id:
            reports = reports.filter(guichetier_id=guichetier_id)

        # Statistiques
        total_reports = reports.count()

        # Grouper par guichetier
        from django.db.models import Sum
        stats_guichetiers = reports.values(
            'guichetier__nom_complet'
        ).annotate(
            nb_reports=Count('id'),
            montant_total=Sum('ancien_billet__montant')
        ).order_by('-nb_reports')

        # Grouper par motif
        stats_motifs = reports.values('motif').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # Liste des guichetiers pour le filtre
        from apps.personnel.models import Utilisateur
        from apps.gares.models import Gare

        # Si l'utilisateur a accès global, afficher tous les guichetiers
        # Sinon, afficher uniquement les guichetiers de sa gare
        if self.request.user.has_global_access:
            guichetiers = Utilisateur.objects.filter(
                role__in=['guichetier', 'gestionnaire', 'chef_gare']
            ).order_by('nom_complet')
            # Liste des gares pour le filtre (uniquement pour accès global)
            gares = Gare.objects.filter(active=True).order_by('nom')
        else:
            guichetiers = Utilisateur.objects.filter(
                role__in=['guichetier', 'gestionnaire', 'chef_gare'],
                gare=self.request.user.gare
            ).order_by('nom_complet')
            gares = None

        context['reports'] = reports.order_by('-date_report')[:100]  # Limiter à 100 derniers
        context['total_reports'] = total_reports
        context['stats_guichetiers'] = stats_guichetiers
        context['stats_motifs'] = stats_motifs
        context['guichetiers'] = guichetiers
        context['gares'] = gares
        context['date_debut'] = date_debut
        context['date_fin'] = date_fin
        context['guichetier_id'] = guichetier_id
        context['gare_id'] = gare_id

        return context
