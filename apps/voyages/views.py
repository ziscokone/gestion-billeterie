from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import timedelta
from core.mixins import GestionRequiredMixin
from .models import Voyage
from .forms import VoyageForm
from apps.compagnie.models import Compagnie
from apps.personnel.models import Chauffeur, Convoyeur
from apps.comptabilite.models import TypeDepense, Depense


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
        context['billets'] = billets
        context['billets_payes'] = billets.filter(statut='paye')
        context['billets_reserves'] = billets.filter(statut='reserve')

        # Calculer les statistiques
        context['nb_billets_payes'] = billets.filter(statut='paye').count()
        context['nb_billets_reserves'] = billets.filter(statut='reserve').count()
        context['montant_total'] = sum(b.montant for b in billets.filter(statut='paye'))

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

        # Récupérer les billets
        billets = voyage.billets.select_related('guichetier').order_by('numero_siege')

        # Récupérer les dépenses du voyage
        depenses = voyage.depenses.select_related('type_depense').order_by('type_depense__ordre', 'type_depense__nom')
        total_depenses = sum(d.montant for d in depenses)

        # Calculer les totaux
        montant_total_billets = sum(b.montant for b in billets.filter(statut='paye'))
        recette_bagages = voyage.recette_bagages or 0
        total_recettes = voyage.get_total_recettes()
        benefice_net = voyage.get_benefice_net()

        context['voyage'] = voyage
        context['billets'] = billets
        context['billets_payes'] = billets.filter(statut='paye')
        context['nb_billets_payes'] = billets.filter(statut='paye').count()
        context['nb_billets_reserves'] = billets.filter(statut='reserve').count()
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

        # Récupérer les billets
        billets = voyage.billets.select_related('destination', 'guichetier').order_by('numero_siege')

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

        # Récupérer les billets avec leurs destinations
        billets = voyage.billets.select_related('destination').all()

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

        # Informations du voyage
        voyage_data = {
            'chauffeur_id': voyage.chauffeur.id if voyage.chauffeur else None,
            'convoyeur_id': voyage.convoyeur.id if voyage.convoyeur else None,
        }

        return JsonResponse({
            'success': True,
            'chauffeurs': chauffeurs_data,
            'convoyeurs': convoyeurs_data,
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

        # Sauvegarder en base de données
        voyage.save(update_fields=['chauffeur', 'convoyeur', 'date_modification'])

        return JsonResponse({
            'success': True,
            'message': 'Agents enregistrés avec succès',
            'chauffeur_nom': voyage.chauffeur.nom_complet if voyage.chauffeur else None,
            'convoyeur_nom': voyage.convoyeur.nom_complet if voyage.convoyeur else None,
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
                'type_depense_nom': d.type_depense.nom,
                'montant': float(d.montant),
                'description': d.description or '',
                'guichetier': d.guichetier.nom_complet if d.guichetier else 'Inconnu',
                'date_creation': d.date_creation.strftime('%d/%m/%Y %H:%M')
            }
            for d in depenses
        ]

        # Calculer le total des dépenses
        total_depenses = sum(d.montant for d in depenses)

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
        total_depenses = sum(d.montant for d in voyage.depenses.all())

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
            montant = float(montant)
            if montant < 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Le montant ne peut pas être négatif'
                }, status=400)
        except (ValueError, TypeError):
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
        total_depenses = sum(d.montant for d in voyage.depenses.all())
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
